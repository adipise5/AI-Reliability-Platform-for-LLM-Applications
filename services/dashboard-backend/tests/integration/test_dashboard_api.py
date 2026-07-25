from __future__ import annotations

from tests.unit.conftest import make_notification, make_run


def test_overview_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get("/api/v1/dashboard/overview")

    assert response.status_code == 401


def test_overview_merges_every_service(client, eval_run_reader, notification_reader):
    run = make_run()
    eval_run_reader.runs[run.id] = run
    notification_reader.notifications = [make_notification()]

    response = client.get("/api/v1/dashboard/overview")

    assert response.status_code == 200
    body = response.json()
    assert "recent_runs" in body
    assert "cost_summary" in body
    assert "budget_status" in body
    assert "latency_anomaly" in body
    assert "recent_notifications" in body
