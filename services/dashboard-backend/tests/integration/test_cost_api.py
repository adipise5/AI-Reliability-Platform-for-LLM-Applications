from __future__ import annotations


def test_cost_summary_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get("/api/v1/cost/summary")

    assert response.status_code == 401


def test_cost_summary_returns_the_summary(client):
    response = client.get("/api/v1/cost/summary")

    assert response.status_code == 200
    assert "total_cost_usd" in response.json()


def test_budget_status_returns_the_status(client):
    response = client.get("/api/v1/cost/budget")

    assert response.status_code == 200
    assert "over_budget" in response.json()
