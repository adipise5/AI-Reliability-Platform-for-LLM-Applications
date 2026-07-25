from __future__ import annotations

from uuid import uuid4

import pytest

from notification_service.application.send_notification import SendNotificationUseCase
from notification_service.domain.entities import NotificationStatus
from notification_service.domain.errors import ChannelDisabledError, ChannelNotFoundError
from tests.unit.conftest import (
    FakeNotificationChannelRepository,
    FakeNotificationRepository,
    FakeTaskQueue,
    make_channel,
)


async def test_creates_a_pending_notification_and_enqueues_it(org_id):
    channel = make_channel(org_id=org_id, enabled=True)
    channel_repo = FakeNotificationChannelRepository([channel])
    notification_repo = FakeNotificationRepository()
    queue = FakeTaskQueue()
    use_case = SendNotificationUseCase(channel_repo, notification_repo, queue)

    notification = await use_case.execute(
        org_id=org_id, channel_id=channel.id, subject="s", body="b"
    )

    assert notification.status == NotificationStatus.PENDING
    assert notification_repo.notifications[notification.id] == notification
    assert queue.enqueued == [notification.id]


async def test_raises_when_channel_missing(org_id):
    use_case = SendNotificationUseCase(
        FakeNotificationChannelRepository(), FakeNotificationRepository(), FakeTaskQueue()
    )

    with pytest.raises(ChannelNotFoundError):
        await use_case.execute(org_id=org_id, channel_id=uuid4(), subject="s", body="b")


async def test_raises_when_channel_belongs_to_a_different_org(org_id):
    channel = make_channel(org_id=uuid4())
    use_case = SendNotificationUseCase(
        FakeNotificationChannelRepository([channel]), FakeNotificationRepository(), FakeTaskQueue()
    )

    with pytest.raises(ChannelNotFoundError):
        await use_case.execute(org_id=org_id, channel_id=channel.id, subject="s", body="b")


async def test_raises_when_channel_disabled(org_id):
    channel = make_channel(org_id=org_id, enabled=False)
    use_case = SendNotificationUseCase(
        FakeNotificationChannelRepository([channel]), FakeNotificationRepository(), FakeTaskQueue()
    )

    with pytest.raises(ChannelDisabledError):
        await use_case.execute(org_id=org_id, channel_id=channel.id, subject="s", body="b")
