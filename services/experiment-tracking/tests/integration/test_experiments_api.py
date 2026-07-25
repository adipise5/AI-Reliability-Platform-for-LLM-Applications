from __future__ import annotations

from uuid import uuid4

from tests.unit.conftest import make_run_summary


def test_create_experiment_requires_authentication(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.post("/api/v1/experiments", json={"name": "e"})

    assert response.status_code == 401


def test_create_experiment_returns_201(client):
    response = client.post("/api/v1/experiments", json={"name": "rollout-v2", "description": "d"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "rollout-v2"
    assert body["run_ids"] == []


def test_create_experiment_rejects_duplicate_name(client):
    client.post("/api/v1/experiments", json={"name": "rollout-v2"})

    response = client.post("/api/v1/experiments", json={"name": "rollout-v2"})

    assert response.status_code == 409
    assert response.json()["type"] == "duplicate_experiment_name"


def test_add_run_rejects_a_run_the_evaluation_engine_does_not_know(client):
    experiment = client.post("/api/v1/experiments", json={"name": "e"}).json()

    response = client.post(f"/api/v1/experiments/{experiment['id']}/runs", json={"run_id": str(uuid4())})

    assert response.status_code == 404
    assert response.json()["type"] == "run_not_found"


def test_add_run_and_compare_round_trip(client, reader):
    run = make_run_summary()
    reader.runs[run.id] = run
    experiment = client.post("/api/v1/experiments", json={"name": "e"}).json()

    added = client.post(f"/api/v1/experiments/{experiment['id']}/runs", json={"run_id": str(run.id)})
    assert added.status_code == 201
    assert added.json()["run_ids"] == [str(run.id)]

    comparison = client.get(f"/api/v1/experiments/{experiment['id']}/comparison")
    assert comparison.status_code == 200
    body = comparison.json()
    assert len(body["runs"]) == 1
    assert body["runs"][0]["id"] == str(run.id)


def test_get_unknown_experiment_returns_404(client):
    response = client.get(f"/api/v1/experiments/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "experiment_not_found"


def test_score_history_returns_matching_runs(client, reader):
    prompt_id = uuid4()
    matching = make_run_summary(prompt_id=prompt_id)
    other = make_run_summary()
    reader.runs[matching.id] = matching
    reader.runs[other.id] = other

    response = client.get("/api/v1/score-history", params={"prompt_id": str(prompt_id)})

    assert response.status_code == 200
    ids = [r["id"] for r in response.json()]
    assert ids == [str(matching.id)]
