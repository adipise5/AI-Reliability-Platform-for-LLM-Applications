from __future__ import annotations

from uuid import uuid4

from notification_service.application.list_notifications import ListNotificationsUseCase
from tests.unit.conftest import FakeNotificationRepository, make_notification


async def test_lists_only_notifications_for_the_org(org_id):
    mine = make_notification(org_id=org_id)
    other = make_notification(org_id=uuid4())
    repo = FakeNotificationRepository([mine, other])
    use_case = ListNotificationsUseCase(repo)

    notifications = await use_case.execute(org_id=org_id)

    assert [n.id for n in notifications] == [mine.id]


async def test_filters_by_channel_id(org_id):
    channel_id = uuid4()
    matching = make_notification(org_id=org_id, channel_id=channel_id)
    other = make_notification(org_id=org_id, channel_id=uuid4())
    repo = FakeNotificationRepository([matching, other])
    use_case = ListNotificationsUseCase(repo)

    notifications = await use_case.execute(org_id=org_id, channel_id=channel_id)

    assert [n.id for n in notifications] == [matching.id]
