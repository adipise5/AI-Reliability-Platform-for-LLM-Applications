"""Use case: create a notification record and hand it to the task queue.

Validates the channel exists, belongs to this org, and is enabled before
enqueueing — cheap checks against data this service already owns, unlike
the Evaluation Engine or Report Generator's triggers, which skip upstream
validation specifically because it would mean a network call to another
service on every request. There's no such call here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from notification_service.domain.entities import Notification, NotificationStatus
from notification_service.domain.errors import ChannelDisabledError, ChannelNotFoundError
from notification_service.domain.ports import (
    NotificationChannelRepository,
    NotificationRepository,
    TaskQueue,
)


class SendNotificationUseCase:
    def __init__(
        self,
        channel_repo: NotificationChannelRepository,
        notification_repo: NotificationRepository,
        task_queue: TaskQueue,
    ) -> None:
        self._channel_repo = channel_repo
        self._notification_repo = notification_repo
        self._task_queue = task_queue

    async def execute(
        self, *, org_id: UUID, channel_id: UUID, subject: str, body: str
    ) -> Notification:
        channel = await self._channel_repo.get_by_id(channel_id)
        if channel is None or channel.org_id != org_id:
            raise ChannelNotFoundError(channel_id)
        if not channel.enabled:
            raise ChannelDisabledError(channel_id)

        notification = Notification(
            id=uuid4(),
            org_id=org_id,
            channel_id=channel_id,
            subject=subject,
            body=body,
            status=NotificationStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        await self._notification_repo.create(notification)
        self._task_queue.enqueue_deliver_notification(notification.id)
        return notification
