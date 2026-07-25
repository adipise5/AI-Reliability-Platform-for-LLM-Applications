"""HTTP client for the Notification Service — implements
`NotificationReader` by forwarding the caller's own bearer credential."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from dashboard_backend.domain.entities import RemoteChannel, RemoteNotification
from dashboard_backend.domain.errors import UpstreamServiceError


class HttpNotificationReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def list_channels(self, credential: str) -> list[RemoteChannel]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/channels",
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("notification-service", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "notification-service", f"GET /channels returned {response.status_code}"
            )
        return [_parse_channel(item) for item in response.json()]

    async def list_notifications(
        self, credential: str, *, channel_id: UUID | None = None
    ) -> list[RemoteNotification]:
        params = {"channel_id": str(channel_id)} if channel_id is not None else {}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/notifications",
                    params=params,
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("notification-service", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "notification-service", f"GET /notifications returned {response.status_code}"
            )
        return [_parse_notification(item) for item in response.json()]


def _parse_channel(payload: dict[str, Any]) -> RemoteChannel:
    return RemoteChannel(
        id=UUID(str(payload["id"])),
        channel_type=str(payload["channel_type"]),
        name=str(payload["name"]),
        target=str(payload["target"]),
        enabled=bool(payload["enabled"]),
    )


def _parse_notification(payload: dict[str, Any]) -> RemoteNotification:
    return RemoteNotification(
        id=UUID(str(payload["id"])),
        channel_id=UUID(str(payload["channel_id"])),
        subject=str(payload["subject"]),
        status=str(payload["status"]),
        created_at=datetime.fromisoformat(str(payload["created_at"])),
    )
