from __future__ import annotations

from uuid import UUID

from dashboard_backend.domain.entities import RemoteNotification
from dashboard_backend.domain.ports import NotificationReader


class ListNotificationsUseCase:
    def __init__(self, notification_reader: NotificationReader) -> None:
        self._notification_reader = notification_reader

    async def execute(
        self, *, credential: str, channel_id: UUID | None = None
    ) -> list[RemoteNotification]:
        return await self._notification_reader.list_notifications(credential, channel_id=channel_id)
