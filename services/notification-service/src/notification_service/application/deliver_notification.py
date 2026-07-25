"""Use case: actually deliver a notification — the work the Celery task
dispatches into. Failure model mirrors the Evaluation Engine's
`ExecuteEvalRunUseCase` and the Report Generator's `GenerateReportUseCase`:
any exception marks the notification FAILED with the error recorded
before re-raising, so Celery still sees the task as errored.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from notification_service.domain.entities import NotificationStatus
from notification_service.domain.ports import (
    NotificationChannelRepository,
    NotificationRepository,
    NotificationSenderRegistry,
)


class DeliverNotificationUseCase:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        channel_repo: NotificationChannelRepository,
        sender_registry: NotificationSenderRegistry,
    ) -> None:
        self._notification_repo = notification_repo
        self._channel_repo = channel_repo
        self._sender_registry = sender_registry

    async def execute(self, notification_id: UUID) -> None:
        notification = await self._notification_repo.get_by_id(notification_id)
        if notification is None:
            return

        channel = await self._channel_repo.get_by_id(notification.channel_id)
        if channel is None:
            failed = replace(
                notification,
                status=NotificationStatus.FAILED,
                error_message=f"channel {notification.channel_id} no longer exists",
                completed_at=datetime.now(UTC),
            )
            await self._notification_repo.update(failed)
            return

        try:
            sender = self._sender_registry.get(channel.channel_type)
            await sender.send(channel, notification)
            sent = replace(
                notification, status=NotificationStatus.SENT, completed_at=datetime.now(UTC)
            )
            await self._notification_repo.update(sent)
        except Exception as exc:
            failed = replace(
                notification,
                status=NotificationStatus.FAILED,
                error_message=str(exc),
                completed_at=datetime.now(UTC),
            )
            await self._notification_repo.update(failed)
            raise
