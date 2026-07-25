from __future__ import annotations

from tests.unit.conftest import make_check


def test_list_checks_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get("/api/v1/github/checks")

    assert response.status_code == 401


def test_list_checks_returns_checks(client, github_checks_reader):
    check = make_check()
    github_checks_reader.checks = [check]

    response = client.get("/api/v1/github/checks")

    assert response.status_code == 200
    assert [c["id"] for c in response.json()] == [str(check.id)]
