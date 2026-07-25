from __future__ import annotations

from uuid import uuid4

import pytest

from notification_service.application.get_channel import GetChannelUseCase
from notification_service.domain.errors import ChannelNotFoundError
from tests.unit.conftest import FakeNotificationChannelRepository, make_channel


async def test_returns_channel_for_the_owning_org(org_id):
    channel = make_channel(org_id=org_id)
    repo = FakeNotificationChannelRepository([channel])
    use_case = GetChannelUseCase(repo)

    result = await use_case.execute(org_id=org_id, channel_id=channel.id)

    assert result.id == channel.id


async def test_raises_when_missing(org_id):
    repo = FakeNotificationChannelRepository()
    use_case = GetChannelUseCase(repo)

    with pytest.raises(ChannelNotFoundError):
        await use_case.execute(org_id=org_id, channel_id=uuid4())


async def test_raises_when_channel_belongs_to_a_different_org(org_id):
    channel = make_channel(org_id=uuid4())
    repo = FakeNotificationChannelRepository([channel])
    use_case = GetChannelUseCase(repo)

    with pytest.raises(ChannelNotFoundError):
        await use_case.execute(org_id=org_id, channel_id=channel.id)
