from __future__ import annotations

from uuid import uuid4

from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from evaluation_engine.api import deps
from evaluation_engine.application.get_run import GetEvalRunUseCase
from evaluation_engine.application.trigger_run import TriggerEvalRunUseCase

PAYLOAD = {
    "prompt_id": str(uuid4()),
    "prompt_version_id": str(uuid4()),
    "dataset_id": str(uuid4()),
    "model": "claude-sonnet-5",
}


def test_trigger_run_requires_authentication(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.post("/api/v1/runs", json=PAYLOAD)

    assert response.status_code == 401


def test_trigger_run_returns_202_and_enqueues(client, repos):
    response = client.post("/api/v1/runs", json=PAYLOAD)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["scorer_names"] == ["exact_match"]
    assert len(repos["queue"].enqueued) == 1
    enqueued_run_id, enqueued_credential = repos["queue"].enqueued[0]
    assert str(enqueued_run_id) == body["id"]
    assert enqueued_credential == "fake-bearer-token"


def test_get_run_returns_the_run_and_its_items(client):
    triggered = client.post("/api/v1/runs", json=PAYLOAD).json()

    fetched = client.get(f"/api/v1/runs/{triggered['id']}")

    assert fetched.status_code == 200
    body = fetched.json()
    assert body["run"]["id"] == triggered["id"]
    assert body["items"] == []


def test_get_unknown_run_returns_404(client):
    response = client.get(f"/api/v1/runs/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "eval_run_not_found"


def test_list_runs_returns_triggered_runs_most_recent_first(client):
    first = client.post("/api/v1/runs", json=PAYLOAD).json()
    second = client.post("/api/v1/runs", json=PAYLOAD).json()

    response = client.get("/api/v1/runs")

    assert response.status_code == 200
    ids = [r["id"] for r in response.json()]
    assert first["id"] in ids
    assert second["id"] in ids


def test_list_runs_filters_by_prompt_id(client):
    triggered = client.post("/api/v1/runs", json=PAYLOAD).json()
    other_payload = {**PAYLOAD, "prompt_id": str(uuid4())}
    client.post("/api/v1/runs", json=other_payload)

    response = client.get("/api/v1/runs", params={"prompt_id": PAYLOAD["prompt_id"]})

    ids = [r["id"] for r in response.json()]
    assert ids == [triggered["id"]]


def test_runs_are_isolated_per_org(app, repos):
    org_a, org_b = uuid4(), uuid4()
    app.dependency_overrides[deps.get_trigger_run_use_case] = lambda: TriggerEvalRunUseCase(
        repos["run"], repos["queue"]
    )
    app.dependency_overrides[deps.get_get_run_use_case] = lambda: GetEvalRunUseCase(
        repos["run"], repos["item"]
    )
    app.dependency_overrides[deps.get_bearer_credential] = lambda: "fake-bearer-token"

    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:a", org_id=str(org_a), scopes=frozenset()
    )
    created = TestClient(app).post("/api/v1/runs", json=PAYLOAD).json()

    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:b", org_id=str(org_b), scopes=frozenset()
    )
    response = TestClient(app).get(f"/api/v1/runs/{created['id']}")

    assert response.status_code == 404
    app.dependency_overrides.clear()
