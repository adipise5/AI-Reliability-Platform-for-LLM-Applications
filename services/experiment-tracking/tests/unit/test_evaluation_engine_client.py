from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from experiment_tracking.domain.errors import RunNotFoundError, UpstreamServiceError
from experiment_tracking.infrastructure.clients.evaluation_engine_client import HttpEvalRunReader

BASE_URL = "http://evaluation-engine.internal"


def _run_payload(run_id):
    return {
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


@respx.mock
async def test_get_run_parses_the_run_field():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/runs/{run_id}").mock(
        return_value=httpx.Response(200, json={"run": _run_payload(run_id), "items": []})
    )
    client = HttpEvalRunReader(BASE_URL)

    summary = await client.get_run("tok", run_id)

    assert summary.id == run_id
    assert summary.status == "completed"
    assert summary.completed_at is not None


@respx.mock
async def test_get_run_raises_run_not_found_on_404():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/runs/{run_id}").mock(
        return_value=httpx.Response(404, json={"type": "eval_run_not_found", "message": "nope"})
    )
    client = HttpEvalRunReader(BASE_URL)

    with pytest.raises(RunNotFoundError):
        await client.get_run("tok", run_id)


@respx.mock
async def test_get_run_raises_upstream_error_on_5xx():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/runs/{run_id}").mock(return_value=httpx.Response(500))
    client = HttpEvalRunReader(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.get_run("tok", run_id)


@respx.mock
async def test_list_runs_parses_a_bare_list_and_sends_filters():
    prompt_id = uuid4()
    route = respx.get(f"{BASE_URL}/api/v1/runs").mock(
        return_value=httpx.Response(200, json=[_run_payload(uuid4())])
    )
    client = HttpEvalRunReader(BASE_URL)

    runs = await client.list_runs("tok", prompt_id=prompt_id)

    assert len(runs) == 1
    assert route.calls.last.request.url.params["prompt_id"] == str(prompt_id)
