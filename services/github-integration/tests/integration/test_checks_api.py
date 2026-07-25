from __future__ import annotations

from uuid import uuid4

from github_integration.domain.entities import CheckStatus
from tests.unit.conftest import make_check, make_gate_decision


def test_get_check_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get(f"/api/v1/checks/{uuid4()}")

    assert response.status_code == 401


def test_get_check_returns_404_for_unknown_id(client):
    response = client.get(f"/api/v1/checks/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "check_not_found"


def test_list_checks_filters_by_repo_and_commit_sha(client, org_id, check_repo):
    matching = make_check(org_id=org_id, repo="acme/widgets", commit_sha="c" * 40)
    other = make_check(org_id=org_id, repo="acme/other", commit_sha="c" * 40)
    check_repo.checks[matching.id] = matching
    check_repo.checks[other.id] = other

    response = client.get(
        "/api/v1/checks", params={"repo": "acme/widgets", "commit_sha": "c" * 40}
    )

    assert response.status_code == 200
    assert [c["id"] for c in response.json()] == [str(matching.id)]


def test_complete_check_round_trip(client, org_id, check_repo, reader, github):
    check = make_check(org_id=org_id)
    check_repo.checks[check.id] = check
    decision = make_gate_decision(verdict="fail")
    reader.decisions[decision.run_id] = decision

    response = client.post(
        f"/api/v1/checks/{check.id}/complete", json={"run_id": str(decision.run_id)}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["conclusion"] == "failure"
    assert len(github.updated_checks) == 1


def test_complete_check_returns_409_when_already_completed(client, org_id, check_repo, reader):
    check = make_check(org_id=org_id, status=CheckStatus.COMPLETED)
    check_repo.checks[check.id] = check

    response = client.post(f"/api/v1/checks/{check.id}/complete", json={"run_id": str(uuid4())})

    assert response.status_code == 409
    assert response.json()["type"] == "check_already_completed"


def test_post_comment_returns_204(client, org_id, check_repo, github):
    check = make_check(org_id=org_id, repo="acme/widgets")
    check_repo.checks[check.id] = check

    response = client.post(
        f"/api/v1/checks/{check.id}/comment", json={"pr_number": 42, "body": "hi"}
    )

    assert response.status_code == 204
    assert github.comments == [("acme/widgets", 42, "hi")]
