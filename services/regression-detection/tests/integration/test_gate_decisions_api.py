from __future__ import annotations

from uuid import uuid4

from tests.unit.conftest import make_run


def test_gate_run_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.post("/api/v1/gate-decisions", json={"run_id": str(uuid4())})

    assert response.status_code == 401


def test_gate_run_returns_pass_for_first_completed_run(client, reader):
    run = make_run(status="completed", aggregate_score=0.9)
    reader.runs[run.id] = run

    response = client.post("/api/v1/gate-decisions", json={"run_id": str(run.id)})

    assert response.status_code == 201
    body = response.json()
    assert body["verdict"] == "pass"
    assert body["run_id"] == str(run.id)


def test_gate_run_returns_upstream_error_for_unknown_run(client):
    response = client.post("/api/v1/gate-decisions", json={"run_id": str(uuid4())})

    assert response.status_code == 502
    assert response.json()["type"] == "upstream_service_error"


def test_gate_run_returns_conflict_for_incomplete_run(client, reader):
    run = make_run(status="running", aggregate_score=None)
    reader.runs[run.id] = run

    response = client.post("/api/v1/gate-decisions", json={"run_id": str(run.id)})

    assert response.status_code == 409
    assert response.json()["type"] == "run_not_completed"


def test_get_gate_decision_round_trip(client, reader):
    run = make_run(status="completed", aggregate_score=0.9)
    reader.runs[run.id] = run
    client.post("/api/v1/gate-decisions", json={"run_id": str(run.id)})

    response = client.get(f"/api/v1/gate-decisions/{run.id}")

    assert response.status_code == 200
    assert response.json()["run_id"] == str(run.id)


def test_get_gate_decision_returns_404_when_never_gated(client):
    response = client.get(f"/api/v1/gate-decisions/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "gate_decision_not_found"
