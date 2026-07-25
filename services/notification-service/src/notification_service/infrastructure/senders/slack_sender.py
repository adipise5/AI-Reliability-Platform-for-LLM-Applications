"""Delivers via a Slack incoming webhook — `channel.target` is that
webhook's URL, which is itself the only credential Slack requires."""

from __future__ import annotations

import httpx

from notification_service.domain.entities import ChannelType, Notification, NotificationChannel
from notification_service.domain.errors import DeliveryError


class SlackWebhookSender:
    channel_type = ChannelType.SLACK

    def __init__(self, *, timeout: float) -> None:
        self._timeout = timeout

    async def send(self, channel: NotificationChannel, notification: Notification) -> None:
        payload = {"text": f"*{notification.subject}*\n{notification.body}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(channel.target, json=payload)
            except httpx.HTTPError as exc:
                raise DeliveryError(self.channel_type.value, str(exc)) from exc

        if response.status_code != 200:
            raise DeliveryError(
                self.channel_type.value, f"webhook returned {response.status_code}"
            )
