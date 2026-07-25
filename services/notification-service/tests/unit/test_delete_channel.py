from __future__ import annotations

from uuid import uuid4

import pytest

from notification_service.application.delete_channel import DeleteChannelUseCase
from notification_service.domain.errors import ChannelNotFoundError
from tests.unit.conftest import FakeNotificationChannelRepository, make_channel


async def test_deletes_the_channel(org_id):
    channel = make_channel(org_id=org_id)
    repo = FakeNotificationChannelRepository([channel])
    use_case = DeleteChannelUseCase(repo)

    await use_case.execute(org_id=org_id, channel_id=channel.id)

    assert channel.id not in repo.channels


async def test_raises_when_missing(org_id):
    repo = FakeNotificationChannelRepository()
    use_case = DeleteChannelUseCase(repo)

    with pytest.raises(ChannelNotFoundError):
        await use_case.execute(org_id=org_id, channel_id=uuid4())


async def test_raises_when_channel_belongs_to_a_different_org(org_id):
    channel = make_channel(org_id=uuid4())
    repo = FakeNotificationChannelRepository([channel])
    use_case = DeleteChannelUseCase(repo)

    with pytest.raises(ChannelNotFoundError):
        await use_case.execute(org_id=org_id, channel_id=channel.id)

    assert channel.id in repo.channels
