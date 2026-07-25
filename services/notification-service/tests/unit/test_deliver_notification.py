from __future__ import annotations

from uuid import uuid4

import pytest

from notification_service.application.deliver_notification import DeliverNotificationUseCase
from notification_service.domain.entities import ChannelType, NotificationStatus
from notification_service.domain.errors import DeliveryError
from tests.unit.conftest import (
    FakeNotificationChannelRepository,
    FakeNotificationRepository,
    FakeSender,
    FakeSenderRegistry,
    make_channel,
    make_notification,
)


async def test_missing_notification_is_a_noop():
    use_case = DeliverNotificationUseCase(
        FakeNotificationRepository(), FakeNotificationChannelRepository(), FakeSenderRegistry([])
    )

    await use_case.execute(uuid4())  # should not raise


async def test_delivers_and_marks_sent():
    channel = make_channel(channel_type=ChannelType.SLACK)
    notification = make_notification(channel_id=channel.id)
    channel_repo = FakeNotificationChannelRepository([channel])
    notification_repo = FakeNotificationRepository([notification])
    sender = FakeSender(ChannelType.SLACK)
    use_case = DeliverNotificationUseCase(
        notification_repo, channel_repo, FakeSenderRegistry([sender])
    )

    await use_case.execute(notification.id)

    updated = notification_repo.notifications[notification.id]
    assert updated.status == NotificationStatus.SENT
    assert updated.completed_at is not None
    assert sender.sent == [(channel, notification)]


async def test_marks_failed_and_reraises_on_delivery_error():
    channel = make_channel(channel_type=ChannelType.EMAIL)
    notification = make_notification(channel_id=channel.id)
    channel_repo = FakeNotificationChannelRepository([channel])
    notification_repo = FakeNotificationRepository([notification])
    sender = FakeSender(ChannelType.EMAIL, error=DeliveryError("email", "smtp refused"))
    use_case = DeliverNotificationUseCase(
        notification_repo, channel_repo, FakeSenderRegistry([sender])
    )

    with pytest.raises(DeliveryError):
        await use_case.execute(notification.id)

    updated = notification_repo.notifications[notification.id]
    assert updated.status == NotificationStatus.FAILED
    assert "smtp refused" in (updated.error_message or "")


async def test_marks_failed_when_channel_no_longer_exists():
    notification = make_notification(channel_id=uuid4())
    notification_repo = FakeNotificationRepository([notification])
    use_case = DeliverNotificationUseCase(
        notification_repo, FakeNotificationChannelRepository(), FakeSenderRegistry([])
    )

    await use_case.execute(notification.id)

    updated = notification_repo.notifications[notification.id]
    assert updated.status == NotificationStatus.FAILED
    assert updated.completed_at is not None
