from __future__ import annotations

import httpx
import pytest
import respx

from dashboard_backend.domain.errors import UpstreamServiceError
from dashboard_backend.infrastructure.clients.trace_collector_client import HttpTraceReader

BASE_URL = "http://trace-collector.internal"


@respx.mock
async def test_list_recent_traces_sends_no_auth_header():
    route = respx.get(f"{BASE_URL}/api/v1/traces").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "trace_id": "abc123",
                    "root_span_name": "gateway.chat",
                    "span_count": 3,
                    "status": "OK",
                    "started_at": "2026-01-01T00:00:00Z",
                    "duration_ms": 120.5,
                }
            ],
        )
    )
    client = HttpTraceReader(BASE_URL, timeout=5.0)

    traces = await client.list_recent_traces(10)

    assert len(traces) == 1
    assert traces[0].trace_id == "abc123"
    assert "authorization" not in route.calls.last.request.headers


@respx.mock
async def test_list_recent_traces_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/traces").mock(return_value=httpx.Response(500))
    client = HttpTraceReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.list_recent_traces(10)
