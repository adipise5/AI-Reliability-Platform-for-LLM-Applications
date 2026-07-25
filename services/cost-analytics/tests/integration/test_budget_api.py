from __future__ import annotations


def test_set_budget_requires_authentication(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.put("/api/v1/budget", json={"monthly_limit_usd": 100.0})

    assert response.status_code == 401


def test_budget_status_before_any_budget_is_set(client):
    response = client.get("/api/v1/budget")

    assert response.status_code == 200
    body = response.json()
    assert body["limit_usd"] is None
    assert body["over_budget"] is False


def test_set_and_check_budget_round_trip(client, org_id):
    set_response = client.put("/api/v1/budget", json={"monthly_limit_usd": 50.0})
    assert set_response.status_code == 200
    assert set_response.json()["monthly_limit_usd"] == 50.0

    client.post(
        "/api/v1/usage-events",
        json={
            "org_id": str(org_id),
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "prompt_tokens": 100000,
            "completion_tokens": 100000,
        },
    )

    status_response = client.get("/api/v1/budget")
    body = status_response.json()
    assert body["limit_usd"] == 50.0
    assert body["spent_this_month_usd"] > 0
