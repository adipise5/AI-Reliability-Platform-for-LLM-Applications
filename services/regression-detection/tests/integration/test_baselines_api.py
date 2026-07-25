from __future__ import annotations

from uuid import uuid4

from tests.unit.conftest import make_run


def test_get_baseline_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get(f"/api/v1/baselines/{uuid4()}")

    assert response.status_code == 401


def test_get_baseline_returns_404_when_no_baseline_yet(client):
    response = client.get(f"/api/v1/baselines/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "baseline_not_found"


def test_get_baseline_returns_the_seeded_baseline_after_gating(client, reader):
    run = make_run(status="completed", aggregate_score=0.9)
    reader.runs[run.id] = run
    client.post("/api/v1/gate-decisions", json={"run_id": str(run.id)})

    response = client.get(f"/api/v1/baselines/{run.prompt_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["prompt_id"] == str(run.prompt_id)
    assert body["mean_score"] == 0.9
