from __future__ import annotations

import httpx
import pytest
import respx

from notification_service.domain.errors import DeliveryError
from notification_service.infrastructure.senders.slack_sender import SlackWebhookSender
from tests.unit.conftest import make_channel, make_notification

WEBHOOK_URL = "https://hooks.slack.example/services/T000/B000/xxx"


@respx.mock
async def test_posts_subject_and_body_as_slack_text():
    route = respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(200, text="ok"))
    channel = make_channel(target=WEBHOOK_URL)
    notification = make_notification(subject="Gate failed", body="details here")
    sender = SlackWebhookSender(timeout=5.0)

    await sender.send(channel, notification)

    sent_payload = route.calls.last.request.content
    assert b"Gate failed" in sent_payload
    assert b"details here" in sent_payload


@respx.mock
async def test_raises_delivery_error_on_non_200():
    respx.post(WEBHOOK_URL).mock(return_value=httpx.Response(400, text="invalid_payload"))
    channel = make_channel(target=WEBHOOK_URL)
    notification = make_notification()
    sender = SlackWebhookSender(timeout=5.0)

    with pytest.raises(DeliveryError):
        await sender.send(channel, notification)


@respx.mock
async def test_raises_delivery_error_on_network_failure():
    respx.post(WEBHOOK_URL).mock(side_effect=httpx.ConnectError("refused"))
    channel = make_channel(target=WEBHOOK_URL)
    notification = make_notification()
    sender = SlackWebhookSender(timeout=5.0)

    with pytest.raises(DeliveryError):
        await sender.send(channel, notification)
