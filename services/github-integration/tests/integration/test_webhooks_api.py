from __future__ import annotations

from tests.integration.conftest import WEBHOOK_SECRET
from tests.unit.conftest import pull_request_payload, signed_payload


def test_rejects_invalid_signature(client, org_id):
    body, _ = signed_payload(WEBHOOK_SECRET, pull_request_payload())

    response = client.post(
        f"/webhooks/github/{org_id}",
        content=body,
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": "sha256=deadbeef"},
    )

    assert response.status_code == 401
    assert response.json()["type"] == "invalid_webhook_signature"


def test_creates_a_check_run_for_an_opened_pr(client, org_id, github):
    body, signature = signed_payload(WEBHOOK_SECRET, pull_request_payload(action="opened"))

    response = client.post(
        f"/webhooks/github/{org_id}",
        content=body,
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": signature},
    )

    assert response.status_code == 200
    body_json = response.json()
    assert body_json["status"] == "queued"
    assert len(github.created_checks) == 1


def test_ignores_unrelated_events(client, org_id, github):
    body, signature = signed_payload(WEBHOOK_SECRET, {"zen": "keep it simple"})

    response = client.post(
        f"/webhooks/github/{org_id}",
        content=body,
        headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": signature},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}
    assert github.created_checks == []
