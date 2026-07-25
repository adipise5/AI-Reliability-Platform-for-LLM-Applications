from __future__ import annotations

import httpx
import pytest
import respx

from hallucination_detection.domain.errors import UpstreamServiceError
from hallucination_detection.infrastructure.gateway_client import HttpGatewayClient

BASE_URL = "http://gateway.internal"


@respx.mock
async def test_complete_returns_the_content_string():
    route = respx.post(f"{BASE_URL}/api/v1/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "provider": "anthropic",
                "model": "claude-sonnet-5",
                "content": "SUPPORTED\nbecause",
                "finish_reason": "end_turn",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 5.0,
            },
        )
    )
    client = HttpGatewayClient(BASE_URL)

    content = await client.complete("tok", model="claude-sonnet-5", prompt="hi")

    assert content == "SUPPORTED\nbecause"
    assert route.calls.last.request.headers["authorization"] == "Bearer tok"


@respx.mock
async def test_complete_raises_on_upstream_error():
    respx.post(f"{BASE_URL}/api/v1/chat").mock(
        return_value=httpx.Response(502, json={"type": "provider_error", "message": "boom"})
    )
    client = HttpGatewayClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.complete("tok", model="m", prompt="hi")


@respx.mock
async def test_complete_raises_on_connection_error():
    respx.post(f"{BASE_URL}/api/v1/chat").mock(side_effect=httpx.ConnectError("refused"))
    client = HttpGatewayClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.complete("tok", model="m", prompt="hi")
