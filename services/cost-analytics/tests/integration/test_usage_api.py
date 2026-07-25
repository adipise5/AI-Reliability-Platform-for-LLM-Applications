from __future__ import annotations

from uuid import uuid4


def test_ingest_usage_event_requires_no_auth(client, org_id):
    response = client.post(
        "/api/v1/usage-events",
        json={
            "org_id": str(org_id),
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        },
    )

    assert response.status_code == 202


def test_get_usage_summary_requires_authentication(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/api/v1/usage")

    assert response.status_code == 401


def test_ingest_then_summarize_round_trip(client, org_id):
    client.post(
        "/api/v1/usage-events",
        json={
            "org_id": str(org_id),
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        },
    )

    response = client.get("/api/v1/usage")

    assert response.status_code == 200
    body = response.json()
    assert body["total_prompt_tokens"] == 1000
    assert body["total_completion_tokens"] == 500
    assert body["total_cost_usd"] > 0
    assert len(body["by_model"]) == 1


def test_usage_is_isolated_per_org(client, org_id):
    other_org = uuid4()
    client.post(
        "/api/v1/usage-events",
        json={
            "org_id": str(other_org),
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "prompt_tokens": 999,
            "completion_tokens": 999,
        },
    )

    response = client.get("/api/v1/usage")

    assert response.json()["total_prompt_tokens"] == 0
