from __future__ import annotations

PAYLOAD = {"org_name": "Acme", "owner_email": "a@acme.example.com", "owner_password": "hunter22222"}


def test_login_then_introspect_round_trip(client):
    registered = client.post("/api/v1/orgs", json=PAYLOAD).json()

    login = client.post(
        "/api/v1/auth/login", json={"email": PAYLOAD["owner_email"], "password": PAYLOAD["owner_password"]}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    introspect = client.post("/api/v1/auth/introspect", json={"credential": token})
    assert introspect.status_code == 200
    body = introspect.json()
    assert body["org_id"] == registered["org_id"]
    assert "org:admin" in body["scopes"]
    assert "chat:write" in body["scopes"]


def test_login_rejects_wrong_password(client):
    client.post("/api/v1/orgs", json=PAYLOAD)

    response = client.post(
        "/api/v1/auth/login", json={"email": PAYLOAD["owner_email"], "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["type"] == "invalid_credentials"


def test_login_rejects_unknown_email(client):
    response = client.post("/api/v1/auth/login", json={"email": "ghost@nowhere.example.com", "password": "x"})

    assert response.status_code == 401


def test_introspect_rejects_garbage_credential(client):
    response = client.post("/api/v1/auth/introspect", json={"credential": "garbage"})

    assert response.status_code == 401
    assert response.json()["type"] == "invalid_token"
