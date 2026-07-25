from __future__ import annotations

from uuid import UUID

from notification_service.domain.entities import NotificationChannel
from notification_service.domain.ports import NotificationChannelRepository


class ListChannelsUseCase:
    def __init__(self, channel_repo: NotificationChannelRepository) -> None:
        self._channel_repo = channel_repo

    async def execute(self, *, org_id: UUID) -> list[NotificationChannel]:
        return await self._channel_repo.list_by_org(org_id)
