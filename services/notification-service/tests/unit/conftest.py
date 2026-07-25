from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from notification_service.domain.entities import (
    ChannelType,
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from notification_service.domain.errors import UnsupportedChannelTypeError
from notification_service.domain.ports import NotificationSender


class FakeNotificationChannelRepository:
    def __init__(self, seed: list[NotificationChannel] | None = None) -> None:
        self.channels: dict[UUID, NotificationChannel] = {c.id: c for c in (seed or [])}

    async def create(self, channel: NotificationChannel) -> None:
        self.channels[channel.id] = channel

    async def get_by_id(self, channel_id: UUID) -> NotificationChannel | None:
        return self.channels.get(channel_id)

    async def list_by_org(self, org_id: UUID) -> list[NotificationChannel]:
        return [c for c in self.channels.values() if c.org_id == org_id]

    async def delete(self, channel_id: UUID) -> None:
        self.channels.pop(channel_id, None)


class FakeNotificationRepository:
    def __init__(self, seed: list[Notification] | None = None) -> None:
        self.notifications: dict[UUID, Notification] = {n.id: n for n in (seed or [])}

    async def create(self, notification: Notification) -> None:
        self.notifications[notification.id] = notification

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        return self.notifications.get(notification_id)

    async def update(self, notification: Notification) -> None:
        self.notifications[notification.id] = notification

    async def list_by_org(
        self, org_id: UUID, *, channel_id: UUID | None = None
    ) -> list[Notification]:
        matches = [n for n in self.notifications.values() if n.org_id == org_id]
        if channel_id is not None:
            matches = [n for n in matches if n.channel_id == channel_id]
        return sorted(matches, key=lambda n: n.created_at, reverse=True)


class FakeTaskQueue:
    def __init__(self) -> None:
        self.enqueued: list[UUID] = []

    def enqueue_deliver_notification(self, notification_id: UUID) -> None:
        self.enqueued.append(notification_id)


class FakeSender:
    def __init__(self, channel_type: ChannelType, error: Exception | None = None) -> None:
        self.channel_type = channel_type
        self._error = error
        self.sent: list[tuple[NotificationChannel, Notification]] = []

    async def send(self, channel: NotificationChannel, notification: Notification) -> None:
        if self._error is not None:
            raise self._error
        self.sent.append((channel, notification))


class FakeSenderRegistry:
    def __init__(self, senders: list[NotificationSender]) -> None:
        self._senders = {s.channel_type: s for s in senders}

    def get(self, channel_type: ChannelType) -> NotificationSender:
        sender = self._senders.get(channel_type)
        if sender is None:
            raise UnsupportedChannelTypeError(channel_type.value)
        return sender


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


def make_channel(**overrides: object) -> NotificationChannel:
    base = NotificationChannel(
        id=uuid4(),
        org_id=uuid4(),
        channel_type=ChannelType.SLACK,
        name="alerts",
        target="https://hooks.slack.example/services/T000/B000/xxx",
        enabled=True,
        created_at=datetime.now(UTC),
    )
    return replace(base, **overrides)


def make_notification(**overrides: object) -> Notification:
    base = Notification(
        id=uuid4(),
        org_id=uuid4(),
        channel_id=uuid4(),
        subject="Gate failed",
        body="Run abc123 dropped below baseline",
        status=NotificationStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    return replace(base, **overrides)
