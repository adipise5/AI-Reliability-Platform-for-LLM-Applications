from __future__ import annotations

import json

import httpx
import respx

from gateway.infrastructure.cost_analytics_usage_sink import HttpCostAnalyticsUsageSink

BASE_URL = "http://cost-analytics.internal"


@respx.mock
async def test_emit_usage_posts_the_usage_event():
    route = respx.post(f"{BASE_URL}/api/v1/usage-events").mock(return_value=httpx.Response(202))
    sink = HttpCostAnalyticsUsageSink(BASE_URL)

    await sink.emit_usage(
        org_id="org-1", provider="anthropic", model="claude-sonnet-5", prompt_tokens=5, completion_tokens=3
    )

    body = json.loads(route.calls.last.request.content)
    assert body == {
        "org_id": "org-1",
        "provider": "anthropic",
        "model": "claude-sonnet-5",
        "prompt_tokens": 5,
        "completion_tokens": 3,
    }


@respx.mock
async def test_emit_usage_swallows_5xx_instead_of_raising():
    respx.post(f"{BASE_URL}/api/v1/usage-events").mock(return_value=httpx.Response(503))
    sink = HttpCostAnalyticsUsageSink(BASE_URL)

    await sink.emit_usage(
        org_id="org-1", provider="anthropic", model="m", prompt_tokens=1, completion_tokens=1
    )  # must not raise


@respx.mock
async def test_emit_usage_swallows_connection_errors_instead_of_raising():
    respx.post(f"{BASE_URL}/api/v1/usage-events").mock(side_effect=httpx.ConnectError("refused"))
    sink = HttpCostAnalyticsUsageSink(BASE_URL)

    await sink.emit_usage(
        org_id="org-1", provider="anthropic", model="m", prompt_tokens=1, completion_tokens=1
    )  # must not raise
