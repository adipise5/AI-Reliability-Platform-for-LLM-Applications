from __future__ import annotations

from uuid import uuid4

from tests.unit.conftest import make_run


def test_list_runs_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get("/api/v1/runs")

    assert response.status_code == 401


def test_list_runs_returns_runs(client, eval_run_reader):
    run = make_run()
    eval_run_reader.runs[run.id] = run

    response = client.get("/api/v1/runs")

    assert response.status_code == 200
    assert [r["id"] for r in response.json()] == [str(run.id)]


def test_get_run_detail_returns_404_for_unknown_run(client):
    response = client.get(f"/api/v1/runs/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "run_not_found"


def test_get_run_detail_returns_the_run(client, eval_run_reader):
    run = make_run()
    eval_run_reader.runs[run.id] = run

    response = client.get(f"/api/v1/runs/{run.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["run"]["id"] == str(run.id)
    assert body["gate_decision"] is None
