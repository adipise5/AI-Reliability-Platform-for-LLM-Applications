from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from dashboard_backend.domain.errors import UpstreamServiceError
from dashboard_backend.infrastructure.clients.notification_client import HttpNotificationReader

BASE_URL = "http://notification-service.internal"


@respx.mock
async def test_list_channels_parses_a_bare_list():
    respx.get(f"{BASE_URL}/api/v1/channels").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": str(uuid4()),
                    "org_id": str(uuid4()),
                    "channel_type": "slack",
                    "name": "alerts",
                    "target": "https://hooks.slack.example/x",
                    "enabled": True,
                    "created_at": "2026-01-01T00:00:00Z",
                }
            ],
        )
    )
    client = HttpNotificationReader(BASE_URL, timeout=5.0)

    channels = await client.list_channels("tok")

    assert len(channels) == 1
    assert channels[0].channel_type == "slack"


@respx.mock
async def test_list_channels_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/channels").mock(return_value=httpx.Response(500))
    client = HttpNotificationReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.list_channels("tok")


@respx.mock
async def test_list_notifications_sends_channel_id_filter():
    channel_id = uuid4()
    route = respx.get(f"{BASE_URL}/api/v1/notifications").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": str(uuid4()),
                    "org_id": str(uuid4()),
                    "channel_id": str(channel_id),
                    "subject": "s",
                    "body": "b",
                    "status": "sent",
                    "error_message": None,
                    "created_at": "2026-01-01T00:00:00Z",
                    "completed_at": "2026-01-01T00:00:01Z",
                }
            ],
        )
    )
    client = HttpNotificationReader(BASE_URL, timeout=5.0)

    notifications = await client.list_notifications("tok", channel_id=channel_id)

    assert len(notifications) == 1
    assert route.calls.last.request.url.params["channel_id"] == str(channel_id)


@respx.mock
async def test_list_notifications_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/notifications").mock(return_value=httpx.Response(500))
    client = HttpNotificationReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.list_notifications("tok")
