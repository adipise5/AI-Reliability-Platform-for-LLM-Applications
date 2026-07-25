from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from report_generator.domain.errors import UpstreamServiceError
from report_generator.infrastructure.clients.experiment_tracking_client import HttpExperimentReader

BASE_URL = "http://experiment-tracking.internal"


def _comparison_payload(experiment_id, run_id):
    return {
        "experiment": {
            "id": str(experiment_id),
            "org_id": str(uuid4()),
            "name": "rollout-v2",
            "description": "d",
            "run_ids": [str(run_id)],
            "created_at": "2026-01-01T00:00:00Z",
        },
        "runs": [
            {
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
        ],
    }


@respx.mock
async def test_get_comparison_parses_experiment_and_runs():
    experiment_id, run_id = uuid4(), uuid4()
    respx.get(f"{BASE_URL}/api/v1/experiments/{experiment_id}/comparison").mock(
        return_value=httpx.Response(200, json=_comparison_payload(experiment_id, run_id))
    )
    client = HttpExperimentReader(BASE_URL, timeout=5.0)

    comparison = await client.get_comparison("tok", experiment_id)

    assert comparison.experiment.id == experiment_id
    assert comparison.experiment.name == "rollout-v2"
    assert len(comparison.runs) == 1
    assert comparison.runs[0].id == run_id
    assert comparison.runs[0].completed_at is not None


@respx.mock
async def test_get_comparison_raises_upstream_error_on_404():
    experiment_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/experiments/{experiment_id}/comparison").mock(
        return_value=httpx.Response(404)
    )
    client = HttpExperimentReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_comparison("tok", experiment_id)


@respx.mock
async def test_get_comparison_raises_upstream_error_on_5xx():
    experiment_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/experiments/{experiment_id}/comparison").mock(
        return_value=httpx.Response(500)
    )
    client = HttpExperimentReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.get_comparison("tok", experiment_id)
