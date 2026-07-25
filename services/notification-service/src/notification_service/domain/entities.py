"""Domain entities for the Notification Service — see ADR-0001: no
framework imports here.

Unlike every other cross-service reader in this project, delivery here
never calls another ARP service — a channel's `target` is an external
destination (a Slack incoming-webhook URL, an email address, an
arbitrary webhook URL), so there's no bearer credential to forward, only
delivery credentials this service already owns (SMTP settings) or none
at all (a webhook URL is the credential).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ChannelType(StrEnum):
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class NotificationChannel:
    id: UUID
    org_id: UUID
    channel_type: ChannelType
    name: str
    target: str
    enabled: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Notification:
    id: UUID
    org_id: UUID
    channel_id: UUID
    subject: str
    body: str
    status: NotificationStatus
    created_at: datetime
    error_message: str | None = None
    completed_at: datetime | None = None
