from __future__ import annotations

import json

import httpx
import pytest
import respx

from notification_service.domain.errors import DeliveryError
from notification_service.infrastructure.senders.webhook_sender import GenericWebhookSender
from tests.unit.conftest import make_channel, make_notification

WEBHOOK_URL = "https://example.com/incoming"


@respx.mock
async def test_posts_subject_and_body_as_json():
    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(202))
    channel = make_channel(target=WEBHOOK_URL)
    notification = make_notification(subject="s", body="b")
    sender = GenericWebhookSender(timeout=5.0)

    await sender.send(channel, notification)

    payload = json.loads(route.calls.last.request.content)
    assert payload == {"subject": "s", "body": "b"}


@respx.mock
async def test_raises_delivery_error_on_non_2xx():
    respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(500))
    channel = make_channel(target=WEBHOOK_URL)
    notification = make_notification()
    sender = GenericWebhookSender(timeout=5.0)

    with pytest.raises(DeliveryError):
        await sender.send(channel, notification)
