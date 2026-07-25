from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from dashboard_backend.domain.errors import RunNotFoundError, UpstreamServiceError
from dashboard_backend.infrastructure.clients.evaluation_engine_client import HttpEvalRunReader

BASE_URL = "http://evaluation-engine.internal"


def _run_payload(run_id, **overrides):
    payload = {
        "id": str(run_id),
        "prompt_id": str(uuid4()),
        "prompt_version_id": str(uuid4()),
        "dataset_id": str(uuid4()),
        "dataset_version": 1,
        "model": "claude-sonnet-5",
        "status": "completed",
        "aggregate_score": 0.9,
        "created_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:01:00Z",
    }
    payload.update(overrides)
    return payload


@respx.mock
async def test_list_runs_parses_a_bare_list():
    respx.get(f"{BASE_URL}/api/v1/runs").mock(
        return_value=httpx.Response(200, json=[_run_payload(uuid4())])
    )
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    runs = await client.list_runs("tok")

    assert len(runs) == 1


@respx.mock
async def test_list_runs_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/runs").mock(return_value=httpx.Response(500))
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.list_runs("tok")


@respx.mock
async def test_get_run_parses_run_and_items():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/runs/{run_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "run": _run_payload(run_id),
                "items": [
                    {
                        "id": str(uuid4()),
                        "dataset_item_id": str(uuid4()),
                        "output": "hi",
                        "latency_ms": 100.0,
                        "scores": [{"scorer_name": "exact_match", "value": 1.0}],
                    }
                ],
            },
        )
    )
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    run, items = await client.get_run("tok", run_id)

    assert run.id == run_id
    assert len(items) == 1
    assert items[0].scores[0].scorer_name == "exact_match"


@respx.mock
async def test_get_run_raises_run_not_found_on_404():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/runs/{run_id}").mock(return_value=httpx.Response(404))
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    with pytest.raises(RunNotFoundError):
        await client.get_run("tok", run_id)
