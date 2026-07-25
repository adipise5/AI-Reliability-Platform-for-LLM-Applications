from __future__ import annotations

from uuid import uuid4

PAYLOAD = {"org_name": "Acme", "owner_email": "owner@acme.example.com", "owner_password": "hunter22222"}


def _login(client) -> dict[str, str]:
    client.post("/api/v1/orgs", json=PAYLOAD)
    token = client.post(
        "/api/v1/auth/login", json={"email": PAYLOAD["owner_email"], "password": PAYLOAD["owner_password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_api_key_requires_a_bearer_token(client):
    response = client.post("/api/v1/api-keys", json={"name": "ci"})

    assert response.status_code == 401


def test_create_use_and_revoke_api_key_round_trip(client):
    headers = _login(client)

    created = client.post("/api/v1/api-keys", json={"name": "ci key"}, headers=headers)
    assert created.status_code == 201
    body = created.json()
    assert body["secret"].startswith(body["prefix"] + ".")

    introspected = client.post("/api/v1/auth/introspect", json={"credential": body["secret"]})
    assert introspected.status_code == 200
    assert sorted(introspected.json()["scopes"]) == sorted(body["scopes"])

    revoked = client.delete(f"/api/v1/api-keys/{body['id']}", headers=headers)
    assert revoked.status_code == 204

    introspected_after_revoke = client.post("/api/v1/auth/introspect", json={"credential": body["secret"]})
    assert introspected_after_revoke.status_code == 401


def test_create_api_key_can_request_a_narrower_scope_set(client):
    headers = _login(client)

    created = client.post(
        "/api/v1/api-keys", json={"name": "narrow", "scopes": ["chat:write"]}, headers=headers
    )

    assert created.status_code == 201
    assert created.json()["scopes"] == ["chat:write"]


def test_create_api_key_rejects_scope_escalation(client):
    headers = _login(client)

    response = client.post(
        "/api/v1/api-keys", json={"name": "escalate", "scopes": ["chat:write", "made:up"]}, headers=headers
    )

    assert response.status_code == 403
    assert response.json()["type"] == "insufficient_scope"


def test_revoke_unknown_key_returns_404(client):
    headers = _login(client)

    response = client.delete(f"/api/v1/api-keys/{uuid4()}", headers=headers)

    assert response.status_code == 404
