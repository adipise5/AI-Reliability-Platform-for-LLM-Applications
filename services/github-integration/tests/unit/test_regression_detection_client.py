from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from github_integration.domain.errors import UpstreamServiceError
from github_integration.infrastructure.clients.regression_detection_client import HttpGateDecisionReader

BASE_URL = "http://regression-detection.internal"


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
    client = HttpGateDecisionReader(BASE_URL, timeout=5.0)

    decision = await client.get_gate_decision("tok", run_id)

    assert decision.run_id == run_id
    assert decision.verdict == "fail"
    assert decision.observed_score == 0.65


@respx.mock
async def test_get_gate_decision_raises_upstream_error_on_404():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/gate-decisions/{run_id}").mock(return_value=httpx.Response(404))
    client = HttpGateDecisionReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_gate_decision("tok", run_id)


@respx.mock
async def test_get_gate_decision_raises_upstream_error_on_5xx():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/gate-decisions/{run_id}").mock(return_value=httpx.Response(500))
    client = HttpGateDecisionReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_gate_decision("tok", run_id)
