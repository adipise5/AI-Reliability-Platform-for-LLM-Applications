from __future__ import annotations

from notification_service.domain.entities import ChannelType
from notification_service.domain.errors import UnsupportedChannelTypeError
from notification_service.domain.ports import NotificationSender


class InMemoryNotificationSenderRegistry:
    def __init__(self, senders: list[NotificationSender]) -> None:
        self._senders = {sender.channel_type: sender for sender in senders}

    def get(self, channel_type: ChannelType) -> NotificationSender:
        sender = self._senders.get(channel_type)
        if sender is None:
            raise UnsupportedChannelTypeError(channel_type.value)
        return sender
