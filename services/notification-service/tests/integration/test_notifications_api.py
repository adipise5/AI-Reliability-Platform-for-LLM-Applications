from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4


def test_send_notification_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.post(
        "/api/v1/notifications", json={"channel_id": str(uuid4()), "subject": "s", "body": "b"}
    )

    assert response.status_code == 401


def test_send_notification_returns_404_for_unknown_channel(client):
    response = client.post(
        "/api/v1/notifications", json={"channel_id": str(uuid4()), "subject": "s", "body": "b"}
    )

    assert response.status_code == 404
    assert response.json()["type"] == "channel_not_found"


def test_send_notification_returns_202_and_enqueues(client, queue):
    channel = client.post(
        "/api/v1/channels",
        json={"channel_type": "slack", "name": "alerts", "target": "https://hooks.slack.example/x"},
    ).json()

    response = client.post(
        "/api/v1/notifications",
        json={"channel_id": channel["id"], "subject": "Gate failed", "body": "details"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert len(queue.enqueued) == 1


def test_send_notification_returns_409_for_disabled_channel(client, channel_repo):
    channel = client.post(
        "/api/v1/channels",
        json={"channel_type": "slack", "name": "alerts", "target": "https://hooks.slack.example/x"},
    ).json()
    stored = channel_repo.channels[UUID(channel["id"])]
    channel_repo.channels[UUID(channel["id"])] = replace(stored, enabled=False)

    response = client.post(
        "/api/v1/notifications",
        json={"channel_id": channel["id"], "subject": "s", "body": "b"},
    )

    assert response.status_code == 409
    assert response.json()["type"] == "channel_disabled"


def test_get_and_list_notifications_round_trip(client):
    channel = client.post(
        "/api/v1/channels",
        json={"channel_type": "webhook", "name": "hook", "target": "https://example/hook"},
    ).json()
    sent = client.post(
        "/api/v1/notifications",
        json={"channel_id": channel["id"], "subject": "s", "body": "b"},
    ).json()

    fetched = client.get(f"/api/v1/notifications/{sent['id']}")
    assert fetched.status_code == 200

    listed = client.get("/api/v1/notifications", params={"channel_id": channel["id"]})
    assert listed.status_code == 200
    assert [n["id"] for n in listed.json()] == [sent["id"]]


def test_get_notification_returns_404_for_unknown_id(client):
    response = client.get(f"/api/v1/notifications/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "notification_not_found"
