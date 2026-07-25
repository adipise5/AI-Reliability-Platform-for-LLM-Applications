from __future__ import annotations

from uuid import uuid4

import pytest

from notification_service.application.get_notification import GetNotificationUseCase
from notification_service.domain.errors import NotificationNotFoundError
from tests.unit.conftest import FakeNotificationRepository, make_notification


async def test_returns_notification_for_the_owning_org(org_id):
    notification = make_notification(org_id=org_id)
    repo = FakeNotificationRepository([notification])
    use_case = GetNotificationUseCase(repo)

    result = await use_case.execute(org_id=org_id, notification_id=notification.id)

    assert result.id == notification.id


async def test_raises_when_missing(org_id):
    repo = FakeNotificationRepository()
    use_case = GetNotificationUseCase(repo)

    with pytest.raises(NotificationNotFoundError):
        await use_case.execute(org_id=org_id, notification_id=uuid4())


async def test_raises_when_notification_belongs_to_a_different_org(org_id):
    notification = make_notification(org_id=uuid4())
    repo = FakeNotificationRepository([notification])
    use_case = GetNotificationUseCase(repo)

    with pytest.raises(NotificationNotFoundError):
        await use_case.execute(org_id=org_id, notification_id=notification.id)
