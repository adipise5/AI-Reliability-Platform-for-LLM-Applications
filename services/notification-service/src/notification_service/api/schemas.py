from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from notification_service.domain.entities import ChannelType, Notification, NotificationChannel


class CreateChannelIn(BaseModel):
    channel_type: ChannelType
    name: str = Field(..., min_length=1, max_length=200)
    target: str = Field(..., min_length=1, max_length=2000)


class ChannelOut(BaseModel):
    id: UUID
    org_id: UUID
    channel_type: ChannelType
    name: str
    target: str
    enabled: bool
    created_at: datetime

    @classmethod
    def from_domain(cls, channel: NotificationChannel) -> ChannelOut:
        return cls(
            id=channel.id,
            org_id=channel.org_id,
            channel_type=channel.channel_type,
            name=channel.name,
            target=channel.target,
            enabled=channel.enabled,
            created_at=channel.created_at,
        )


class SendNotificationIn(BaseModel):
    channel_id: UUID
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)


class NotificationOut(BaseModel):
    id: UUID
    org_id: UUID
    channel_id: UUID
    subject: str
    body: str
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, notification: Notification) -> NotificationOut:
        return cls(
            id=notification.id,
            org_id=notification.org_id,
            channel_id=notification.channel_id,
            subject=notification.subject,
            body=notification.body,
            status=notification.status.value,
            error_message=notification.error_message,
            created_at=notification.created_at,
            completed_at=notification.completed_at,
        )


class ErrorOut(BaseModel):
    type: str
    message: str
