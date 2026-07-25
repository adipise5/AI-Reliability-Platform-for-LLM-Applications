from __future__ import annotations

from uuid import UUID

from notification_service.domain.entities import Notification
from notification_service.domain.ports import NotificationRepository


class ListNotificationsUseCase:
    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._notification_repo = notification_repo

    async def execute(self, *, org_id: UUID, channel_id: UUID | None = None) -> list[Notification]:
        return await self._notification_repo.list_by_org(org_id, channel_id=channel_id)
