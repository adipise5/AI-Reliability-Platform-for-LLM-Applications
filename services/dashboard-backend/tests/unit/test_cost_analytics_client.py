from __future__ import annotations

import httpx
import pytest
import respx

from dashboard_backend.domain.errors import UpstreamServiceError
from dashboard_backend.infrastructure.clients.cost_analytics_client import HttpCostReader

BASE_URL = "http://cost-analytics.internal"


@respx.mock
async def test_get_usage_summary_parses_the_response():
    respx.get(f"{BASE_URL}/api/v1/usage").mock(
        return_value=httpx.Response(
            200,
            json={
                "total_cost_usd": 1.5,
                "total_prompt_tokens": 100,
                "total_completion_tokens": 50,
                "by_model": [
                    {
                        "provider": "anthropic",
                        "model": "claude-sonnet-5",
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "cost_usd": 1.5,
                    }
                ],
            },
        )
    )
    client = HttpCostReader(BASE_URL, timeout=5.0)

    summary = await client.get_usage_summary("tok")

    assert summary.total_cost_usd == 1.5
    assert len(summary.by_model) == 1


@respx.mock
async def test_get_usage_summary_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/usage").mock(return_value=httpx.Response(500))
    client = HttpCostReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_usage_summary("tok")


@respx.mock
async def test_get_budget_status_parses_the_response():
    respx.get(f"{BASE_URL}/api/v1/budget").mock(
        return_value=httpx.Response(
            200,
            json={
                "spent_this_month_usd": 10.0,
                "limit_usd": 100.0,
                "remaining_usd": 90.0,
                "over_budget": False,
            },
        )
    )
    client = HttpCostReader(BASE_URL, timeout=5.0)

    status = await client.get_budget_status("tok")

    assert status.over_budget is False
    assert status.remaining_usd == 90.0


@respx.mock
async def test_get_budget_status_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/budget").mock(return_value=httpx.Response(500))
    client = HttpCostReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_budget_status("tok")
