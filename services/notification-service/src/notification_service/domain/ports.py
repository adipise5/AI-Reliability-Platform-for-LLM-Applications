"""Ports: interfaces the application layer depends on.

`NotificationSender` is the one port whose adapters talk to the outside
world rather than another bounded context — Slack's incoming-webhook API,
an SMTP relay, or an arbitrary webhook URL. It's still a port for the same
reason: the application layer shouldn't know or care which transport a
channel uses, and a fake makes `DeliverNotificationUseCase` testable
without ever making a real network call.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from notification_service.domain.entities import ChannelType, Notification, NotificationChannel


class NotificationChannelRepository(Protocol):
    async def create(self, channel: NotificationChannel) -> None: ...

    async def get_by_id(self, channel_id: UUID) -> NotificationChannel | None: ...

    async def list_by_org(self, org_id: UUID) -> list[NotificationChannel]: ...

    async def delete(self, channel_id: UUID) -> None: ...


class NotificationRepository(Protocol):
    async def create(self, notification: Notification) -> None: ...

    async def get_by_id(self, notification_id: UUID) -> Notification | None: ...

    async def update(self, notification: Notification) -> None:
        """Persists the full row — callers read-modify-write via
        `dataclasses.replace`, since `Notification` is immutable."""
        ...

    async def list_by_org(
        self, org_id: UUID, *, channel_id: UUID | None = None
    ) -> list[Notification]:
        """Ordered most-recent-first."""
        ...


class NotificationSender(Protocol):
    channel_type: ChannelType

    async def send(self, channel: NotificationChannel, notification: Notification) -> None:
        """Raises `notification_service.domain.errors.DeliveryError` on
        any failure to reach or be accepted by the destination."""
        ...


class NotificationSenderRegistry(Protocol):
    def get(self, channel_type: ChannelType) -> NotificationSender:
        """Raises
        `notification_service.domain.errors.UnsupportedChannelTypeError`
        if `channel_type` isn't registered."""
        ...


class TaskQueue(Protocol):
    def enqueue_deliver_notification(self, notification_id: UUID) -> None: ...
