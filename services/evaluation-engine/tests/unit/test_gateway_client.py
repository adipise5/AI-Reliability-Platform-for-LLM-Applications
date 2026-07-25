from __future__ import annotations

import httpx
import pytest
import respx

from evaluation_engine.domain.errors import UpstreamServiceError
from evaluation_engine.infrastructure.clients.gateway_client import HttpGatewayClient

BASE_URL = "http://gateway.internal"


@respx.mock
async def test_complete_sends_a_single_user_message_and_parses_usage():
    route = respx.post(f"{BASE_URL}/api/v1/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "provider": "anthropic",
                "model": "claude-sonnet-5",
                "content": "42",
                "finish_reason": "end_turn",
                "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
                "latency_ms": 12.5,
            },
        )
    )
    client = HttpGatewayClient(BASE_URL)

    completion = await client.complete(
        "tok", model="claude-sonnet-5", prompt="what is 40+2?", temperature=0.0, max_tokens=10
    )

    assert completion.content == "42"
    assert completion.prompt_tokens == 5
    assert completion.completion_tokens == 1
    sent_body = route.calls.last.request.content
    assert b'"role":"user"' in sent_body
    assert b'"max_tokens":10' in sent_body


@respx.mock
async def test_complete_raises_on_upstream_error():
    respx.post(f"{BASE_URL}/api/v1/chat").mock(
        return_value=httpx.Response(502, json={"type": "provider_error", "message": "boom"})
    )
    client = HttpGatewayClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.complete("tok", model="x", prompt="hi", temperature=1.0, max_tokens=None)


@respx.mock
async def test_complete_raises_on_connection_error():
    respx.post(f"{BASE_URL}/api/v1/chat").mock(side_effect=httpx.ConnectError("refused"))
    client = HttpGatewayClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.complete("tok", model="x", prompt="hi", temperature=1.0, max_tokens=None)
