from __future__ import annotations

from uuid import uuid4

from dashboard_backend.application.list_notifications import ListNotificationsUseCase
from tests.unit.conftest import FakeNotificationReader, make_notification


async def test_filters_by_channel_id():
    channel_id = uuid4()
    matching = make_notification(channel_id=channel_id)
    other = make_notification()
    use_case = ListNotificationsUseCase(FakeNotificationReader(notifications=[matching, other]))

    result = await use_case.execute(credential="tok", channel_id=channel_id)

    assert [n.id for n in result] == [matching.id]
