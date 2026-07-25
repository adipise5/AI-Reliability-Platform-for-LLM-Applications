from __future__ import annotations

from uuid import UUID

from notification_service.domain.entities import Notification
from notification_service.domain.errors import NotificationNotFoundError
from notification_service.domain.ports import NotificationRepository


class GetNotificationUseCase:
    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._notification_repo = notification_repo

    async def execute(self, *, org_id: UUID, notification_id: UUID) -> Notification:
        notification = await self._notification_repo.get_by_id(notification_id)
        if notification is None or notification.org_id != org_id:
            raise NotificationNotFoundError(notification_id)
        return notification
