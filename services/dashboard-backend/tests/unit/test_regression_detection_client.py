from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from dashboard_backend.domain.errors import UpstreamServiceError
from dashboard_backend.infrastructure.clients.regression_detection_client import HttpRegressionReader

BASE_URL = "http://regression-detection.internal"


@respx.mock
async def test_get_baseline_returns_none_on_404():
    prompt_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/baselines/{prompt_id}").mock(return_value=httpx.Response(404))
    client = HttpRegressionReader(BASE_URL, timeout=5.0)

    result = await client.get_baseline("tok", prompt_id)

    assert result is None


@respx.mock
async def test_get_baseline_parses_the_response():
    prompt_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/baselines/{prompt_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(uuid4()),
                "org_id": str(uuid4()),
                "prompt_id": str(prompt_id),
                "mean_score": 0.9,
                "stddev_score": 0.05,
                "sample_size": 5,
                "updated_at": "2026-01-01T00:00:00Z",
            },
        )
    )
    client = HttpRegressionReader(BASE_URL, timeout=5.0)

    result = await client.get_baseline("tok", prompt_id)

    assert result is not None
    assert result.sample_size == 5


@respx.mock
async def test_get_baseline_raises_upstream_error_on_5xx():
    prompt_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/baselines/{prompt_id}").mock(return_value=httpx.Response(500))
    client = HttpRegressionReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_baseline("tok", prompt_id)


@respx.mock
async def test_get_gate_decision_returns_none_on_404():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/gate-decisions/{run_id}").mock(return_value=httpx.Response(404))
    client = HttpRegressionReader(BASE_URL, timeout=5.0)

    result = await client.get_gate_decision("tok", run_id)

    assert result is None


@respx.mock
async def test_get_gate_decision_parses_the_response():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/gate-decisions/{run_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(uuid4()),
                "org_id": str(uuid4()),
                "prompt_id": str(uuid4()),
                "run_id": str(run_id),
                "observed_score": 0.65,
                "baseline_mean": 0.9,
                "baseline_stddev": 0.1,
                "verdict": "fail",
                "created_at": "2026-01-01T00:00:00Z",
            },
        )
    )
    client = HttpRegressionReader(BASE_URL, timeout=5.0)

    result = await client.get_gate_decision("tok", run_id)

    assert result is not None
    assert result.verdict == "fail"


@respx.mock
async def test_get_latency_anomaly_sends_no_auth_header():
    route = respx.get(f"{BASE_URL}/api/v1/latency-anomaly").mock(
        return_value=httpx.Response(
            200,
            json={
                "sample_count": 10,
                "recent_mean_ms": 120.0,
                "baseline_mean_ms": 100.0,
                "baseline_stddev_ms": 10.0,
                "is_anomalous": False,
                "insufficient_data": False,
            },
        )
    )
    client = HttpRegressionReader(BASE_URL, timeout=5.0)

    result = await client.get_latency_anomaly()

    assert result.is_anomalous is False
    assert "authorization" not in route.calls.last.request.headers


@respx.mock
async def test_get_latency_anomaly_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/latency-anomaly").mock(return_value=httpx.Response(500))
    client = HttpRegressionReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_latency_anomaly()
