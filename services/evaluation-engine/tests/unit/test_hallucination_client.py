from __future__ import annotations

import httpx
import pytest
import respx

from evaluation_engine.domain.errors import UpstreamServiceError
from evaluation_engine.infrastructure.clients.hallucination_client import HttpHallucinationDetectionClient

BASE_URL = "http://hallucination.internal"


@respx.mock
async def test_check_faithfulness_returns_score_and_claim_count():
    respx.post(f"{BASE_URL}/api/v1/faithfulness-checks").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "00000000-0000-0000-0000-000000000000",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "response": "r",
                "context": "c",
                "claims": [{"text": "x", "verdict": "supported", "evidence": None}],
                "faithfulness_score": 1.0,
                "created_at": "2026-01-01T00:00:00Z",
            },
        )
    )
    client = HttpHallucinationDetectionClient(BASE_URL)

    score, claim_count = await client.check_faithfulness(
        "tok", model="claude-sonnet-5", response="r", context="c"
    )

    assert score == 1.0
    assert claim_count == 1


@respx.mock
async def test_check_faithfulness_raises_on_upstream_error():
    respx.post(f"{BASE_URL}/api/v1/faithfulness-checks").mock(
        return_value=httpx.Response(502, json={"type": "x", "message": "boom"})
    )
    client = HttpHallucinationDetectionClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.check_faithfulness("tok", model="m", response="r", context="c")


@respx.mock
async def test_check_faithfulness_raises_on_connection_error():
    respx.post(f"{BASE_URL}/api/v1/faithfulness-checks").mock(side_effect=httpx.ConnectError("refused"))
    client = HttpHallucinationDetectionClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.check_faithfulness("tok", model="m", response="r", context="c")
