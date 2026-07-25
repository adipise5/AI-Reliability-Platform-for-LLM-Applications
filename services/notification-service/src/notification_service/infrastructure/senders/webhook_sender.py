"""Delivers to an arbitrary webhook URL — unlike Slack, there's no
platform-specific payload contract, so this just POSTs the notification's
own fields as JSON."""

from __future__ import annotations

import httpx

from notification_service.domain.entities import ChannelType, Notification, NotificationChannel
from notification_service.domain.errors import DeliveryError


class GenericWebhookSender:
    channel_type = ChannelType.WEBHOOK

    def __init__(self, *, timeout: float) -> None:
        self._timeout = timeout

    async def send(self, channel: NotificationChannel, notification: Notification) -> None:
        payload = {"subject": notification.subject, "body": notification.body}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(channel.target, json=payload)
            except httpx.HTTPError as exc:
                raise DeliveryError(self.channel_type.value, str(exc)) from exc

        if not 200 <= response.status_code < 300:
            raise DeliveryError(
                self.channel_type.value, f"webhook returned {response.status_code}"
            )
