from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from regression_detection.domain.errors import UpstreamServiceError
from regression_detection.infrastructure.clients.evaluation_engine_client import HttpEvalRunReader

BASE_URL = "http://evaluation-engine.internal"


def _run_payload(run_id, **overrides):
    payload = {
        "id": str(run_id),
        "prompt_id": str(uuid4()),
        "status": "completed",
        "aggregate_score": 0.9,
    }
    payload.update(overrides)
    return payload


@respx.mock
async def test_get_run_parses_the_run_field():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/runs/{run_id}").mock(
        return_value=httpx.Response(200, json={"run": _run_payload(run_id), "items": []})
    )
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    run = await client.get_run("tok", run_id)

    assert run.id == run_id
    assert run.status == "completed"
    assert run.aggregate_score == 0.9


@respx.mock
async def test_get_run_raises_upstream_error_on_404():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/runs/{run_id}").mock(return_value=httpx.Response(404))
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_run("tok", run_id)


@respx.mock
async def test_get_run_raises_upstream_error_on_5xx():
    run_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/runs/{run_id}").mock(return_value=httpx.Response(500))
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_run("tok", run_id)


@respx.mock
async def test_list_runs_parses_a_bare_list_and_sends_prompt_id():
    prompt_id = uuid4()
    route = respx.get(f"{BASE_URL}/api/v1/runs").mock(
        return_value=httpx.Response(200, json=[_run_payload(uuid4(), prompt_id=str(prompt_id))])
    )
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    runs = await client.list_runs("tok", prompt_id=prompt_id)

    assert len(runs) == 1
    assert route.calls.last.request.url.params["prompt_id"] == str(prompt_id)


@respx.mock
async def test_list_runs_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/runs").mock(return_value=httpx.Response(500))
    client = HttpEvalRunReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.list_runs("tok", prompt_id=uuid4())
