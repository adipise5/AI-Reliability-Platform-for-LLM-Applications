from __future__ import annotations

from tests.unit.conftest import make_channel, make_notification


def test_list_channels_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get("/api/v1/notifications/channels")

    assert response.status_code == 401


def test_list_channels_returns_channels(client, notification_reader):
    channel = make_channel()
    notification_reader.channels = [channel]

    response = client.get("/api/v1/notifications/channels")

    assert response.status_code == 200
    assert [c["id"] for c in response.json()] == [str(channel.id)]


def test_list_notifications_returns_notifications(client, notification_reader):
    notification = make_notification()
    notification_reader.notifications = [notification]

    response = client.get("/api/v1/notifications")

    assert response.status_code == 200
    assert [n["id"] for n in response.json()] == [str(notification.id)]
