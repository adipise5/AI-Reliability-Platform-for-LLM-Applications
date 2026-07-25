from __future__ import annotations

from uuid import uuid4


def test_create_prompt_requires_authentication(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.post("/api/v1/prompts", json={"name": "support-agent"})

    assert response.status_code == 401


def test_create_prompt_returns_201(client):
    response = client.post("/api/v1/prompts", json={"name": "support-agent"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "support-agent"


def test_create_prompt_rejects_duplicate_name(client):
    client.post("/api/v1/prompts", json={"name": "support-agent"})

    response = client.post("/api/v1/prompts", json={"name": "support-agent"})

    assert response.status_code == 409
    assert response.json()["type"] == "duplicate_prompt_name"


def test_full_version_lifecycle(client):
    prompt = client.post("/api/v1/prompts", json={"name": "support-agent"}).json()
    prompt_id = prompt["id"]

    v1 = client.post(
        f"/api/v1/prompts/{prompt_id}/versions",
        json={"template": "You are a helpful bot.", "semver_tag": "v1"},
    )
    assert v1.status_code == 201
    v1_id = v1.json()["id"]

    v2 = client.post(
        f"/api/v1/prompts/{prompt_id}/versions",
        json={"template": "You are a very helpful bot.", "semver_tag": "v2"},
    )
    assert v2.status_code == 201
    v2_id = v2.json()["id"]

    promoted = client.post(
        f"/api/v1/prompts/{prompt_id}/promotions",
        json={"version_id": v2_id, "environment": "prod"},
    )
    assert promoted.status_code == 201

    active = client.get(f"/api/v1/prompts/{prompt_id}/versions/active?environment=prod")
    assert active.status_code == 200
    assert active.json()["id"] == v2_id

    no_active = client.get(f"/api/v1/prompts/{prompt_id}/versions/active?environment=staging")
    assert no_active.status_code == 404
    assert no_active.json()["type"] == "no_active_version"

    diff = client.get(f"/api/v1/prompts/{prompt_id}/versions/diff?a={v1_id}&b={v2_id}")
    assert diff.status_code == 200
    joined = "\n".join(diff.json()["unified_diff"])
    assert "-You are a helpful bot." in joined
    assert "+You are a very helpful bot." in joined

    fetched_v1 = client.get(f"/api/v1/prompts/{prompt_id}/versions/{v1_id}")
    assert fetched_v1.status_code == 200
    assert fetched_v1.json()["template"] == "You are a helpful bot."

    missing = client.get(f"/api/v1/prompts/{prompt_id}/versions/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["type"] == "prompt_version_not_found"


def test_operations_on_unknown_prompt_return_404(client):
    response = client.post(
        f"/api/v1/prompts/{uuid4()}/versions", json={"template": "hi"}
    )

    assert response.status_code == 404
    assert response.json()["type"] == "prompt_not_found"


def test_prompts_are_isolated_per_org(app, repos):
    from auth_client.models import IntrospectionResult
    from fastapi.testclient import TestClient

    from prompt_registry.api import deps

    org_a, org_b = uuid4(), uuid4()
    app.dependency_overrides[deps.get_prompt_repo] = lambda: repos["prompt"]
    app.dependency_overrides[deps.get_version_repo] = lambda: repos["version"]
    app.dependency_overrides[deps.get_promotion_repo] = lambda: repos["promotion"]

    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:a", org_id=str(org_a), scopes=frozenset()
    )
    client_a = TestClient(app)
    created = client_a.post("/api/v1/prompts", json={"name": "support-agent"}).json()

    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:b", org_id=str(org_b), scopes=frozenset()
    )
    client_b = TestClient(app)
    response = client_b.post(
        f"/api/v1/prompts/{created['id']}/versions", json={"template": "hi"}
    )

    assert response.status_code == 404
    app.dependency_overrides.clear()
