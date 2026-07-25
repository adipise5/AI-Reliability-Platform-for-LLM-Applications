from __future__ import annotations

from uuid import uuid4

PAYLOAD = {
    "model": "claude-sonnet-5",
    "response": "Paris is the capital of France.",
    "context": "France's capital is Paris.",
}


def test_check_requires_authentication(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.post("/api/v1/faithfulness-checks", json=PAYLOAD)

    assert response.status_code == 401


def test_check_returns_the_full_result(client):
    response = client.post("/api/v1/faithfulness-checks", json=PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["faithfulness_score"] == 1.0
    assert len(body["claims"]) == 1
    assert body["claims"][0]["verdict"] == "supported"


def test_get_check_returns_a_previously_created_check(client):
    created = client.post("/api/v1/faithfulness-checks", json=PAYLOAD).json()

    fetched = client.get(f"/api/v1/faithfulness-checks/{created['id']}")

    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]


def test_get_unknown_check_returns_404(client):
    response = client.get(f"/api/v1/faithfulness-checks/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "faithfulness_check_not_found"
