from __future__ import annotations

from uuid import uuid4

from notification_service.application.list_channels import ListChannelsUseCase
from tests.unit.conftest import FakeNotificationChannelRepository, make_channel


async def test_lists_only_channels_for_the_org(org_id):
    mine = make_channel(org_id=org_id)
    other = make_channel(org_id=uuid4())
    repo = FakeNotificationChannelRepository([mine, other])
    use_case = ListChannelsUseCase(repo)

    channels = await use_case.execute(org_id=org_id)

    assert [c.id for c in channels] == [mine.id]
