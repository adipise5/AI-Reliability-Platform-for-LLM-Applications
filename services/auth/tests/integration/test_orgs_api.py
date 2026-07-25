from __future__ import annotations

PAYLOAD = {"org_name": "Acme", "owner_email": "owner@acme.example.com", "owner_password": "hunter22222"}


def test_register_org_returns_201_and_persists(client, repos):
    response = client.post("/api/v1/orgs", json=PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["org_name"] == "Acme"
    assert body["owner_email"] == "owner@acme.example.com"
    assert len(repos["user"].users) == 1
    assert len(repos["org"].orgs) == 1


def test_register_org_rejects_duplicate_email(client):
    client.post("/api/v1/orgs", json=PAYLOAD)

    response = client.post("/api/v1/orgs", json={**PAYLOAD, "org_name": "Other Co"})

    assert response.status_code == 409
    assert response.json()["type"] == "email_already_registered"


def test_register_org_rejects_a_short_password(client):
    response = client.post("/api/v1/orgs", json={**PAYLOAD, "owner_password": "short"})

    assert response.status_code == 422
