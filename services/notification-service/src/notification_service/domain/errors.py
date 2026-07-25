from __future__ import annotations

from uuid import UUID


class NotificationServiceError(Exception):
    """Base class for all domain errors raised by this service."""


class ChannelNotFoundError(NotificationServiceError):
    def __init__(self, channel_id: UUID) -> None:
        self.channel_id = channel_id
        super().__init__(f"no channel {channel_id} in this org")


class ChannelDisabledError(NotificationServiceError):
    def __init__(self, channel_id: UUID) -> None:
        self.channel_id = channel_id
        super().__init__(f"channel {channel_id} is disabled")


class NotificationNotFoundError(NotificationServiceError):
    def __init__(self, notification_id: UUID) -> None:
        self.notification_id = notification_id
        super().__init__(f"no notification {notification_id} in this org")


class UnsupportedChannelTypeError(NotificationServiceError):
    def __init__(self, channel_type: str) -> None:
        self.channel_type = channel_type
        super().__init__(f"no sender registered for channel type {channel_type!r}")


class DeliveryError(NotificationServiceError):
    def __init__(self, channel_type: str, message: str) -> None:
        self.channel_type = channel_type
        super().__init__(f"[{channel_type}] delivery failed: {message}")
