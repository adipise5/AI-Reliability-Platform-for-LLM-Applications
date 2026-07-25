from __future__ import annotations

from dashboard_backend.application.list_channels import ListChannelsUseCase
from tests.unit.conftest import FakeNotificationReader, make_channel


async def test_returns_channels_from_the_reader():
    channel = make_channel()
    use_case = ListChannelsUseCase(FakeNotificationReader(channels=[channel]))

    result = await use_case.execute(credential="tok")

    assert result == [channel]
