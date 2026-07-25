from __future__ import annotations

from dashboard_backend.domain.entities import RemoteChannel
from dashboard_backend.domain.ports import NotificationReader


class ListChannelsUseCase:
    def __init__(self, notification_reader: NotificationReader) -> None:
        self._notification_reader = notification_reader

    async def execute(self, *, credential: str) -> list[RemoteChannel]:
        return await self._notification_reader.list_channels(credential)
