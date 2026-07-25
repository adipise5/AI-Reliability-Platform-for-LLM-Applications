from __future__ import annotations

from notification_service.application.create_channel import CreateChannelUseCase
from notification_service.domain.entities import ChannelType
from tests.unit.conftest import FakeNotificationChannelRepository


async def test_creates_an_enabled_channel(org_id):
    repo = FakeNotificationChannelRepository()
    use_case = CreateChannelUseCase(repo)

    channel = await use_case.execute(
        org_id=org_id, channel_type=ChannelType.SLACK, name="alerts", target="https://example/hook"
    )

    assert channel.enabled is True
    assert channel.org_id == org_id
    assert repo.channels[channel.id] == channel
