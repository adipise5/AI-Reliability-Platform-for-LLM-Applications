from __future__ import annotations

from uuid import uuid4


def test_create_channel_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.post(
        "/api/v1/channels", json={"channel_type": "slack", "name": "alerts", "target": "https://x"}
    )

    assert response.status_code == 401


def test_create_and_get_channel(client):
    created = client.post(
        "/api/v1/channels",
        json={"channel_type": "slack", "name": "alerts", "target": "https://hooks.slack.example/x"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["enabled"] is True

    fetched = client.get(f"/api/v1/channels/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_get_channel_returns_404_for_unknown_id(client):
    response = client.get(f"/api/v1/channels/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "channel_not_found"


def test_list_channels_returns_created_channels(client):
    client.post(
        "/api/v1/channels", json={"channel_type": "email", "name": "oncall", "target": "a@b.com"}
    )

    response = client.get("/api/v1/channels")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_channel_removes_it(client):
    created = client.post(
        "/api/v1/channels", json={"channel_type": "webhook", "name": "hook", "target": "https://x"}
    ).json()

    deleted = client.delete(f"/api/v1/channels/{created['id']}")
    assert deleted.status_code == 204

    response = client.get(f"/api/v1/channels/{created['id']}")
    assert response.status_code == 404
