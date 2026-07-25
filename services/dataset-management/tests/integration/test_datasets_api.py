from __future__ import annotations

from uuid import uuid4


def test_create_dataset_requires_authentication(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.post("/api/v1/datasets", json={"name": "qa-golden-set"})

    assert response.status_code == 401


def test_create_dataset_returns_201(client):
    response = client.post("/api/v1/datasets", json={"name": "qa-golden-set"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "qa-golden-set"
    assert body["current_version"] == 0


def test_create_dataset_rejects_duplicate_name(client):
    client.post("/api/v1/datasets", json={"name": "qa-golden-set"})

    response = client.post("/api/v1/datasets", json={"name": "qa-golden-set"})

    assert response.status_code == 409
    assert response.json()["type"] == "duplicate_dataset_name"


def test_bulk_import_rejects_an_empty_batch(client):
    dataset = client.post("/api/v1/datasets", json={"name": "qa-golden-set"}).json()

    response = client.post(f"/api/v1/datasets/{dataset['id']}/items:bulk", json={"items": []})

    assert response.status_code == 422  # min_length=1 on the request schema


def test_full_import_and_list_lifecycle(client):
    dataset = client.post("/api/v1/datasets", json={"name": "qa-golden-set"}).json()
    dataset_id = dataset["id"]

    first_import = client.post(
        f"/api/v1/datasets/{dataset_id}/items:bulk",
        json={"items": [{"input": {"q": "2+2"}, "expected_output": "4"}]},
    )
    assert first_import.status_code == 201
    assert first_import.json() == {"dataset_id": dataset_id, "version": 1, "item_count": 1}

    second_import = client.post(
        f"/api/v1/datasets/{dataset_id}/items:bulk",
        json={
            "items": [
                {"input": {"q": "3+3"}, "expected_output": "6"},
                {"input": {"q": "4+4"}, "expected_output": "8"},
            ]
        },
    )
    assert second_import.status_code == 201
    assert second_import.json()["version"] == 2

    dataset_after = client.get(f"/api/v1/datasets/{dataset_id}").json()
    assert dataset_after["current_version"] == 2

    current_items = client.get(f"/api/v1/datasets/{dataset_id}/items").json()
    assert len(current_items) == 2

    v1_items = client.get(f"/api/v1/datasets/{dataset_id}/items?version=1").json()
    assert len(v1_items) == 1
    assert v1_items[0]["expected_output"] == "4"


def test_operations_on_unknown_dataset_return_404(client):
    response = client.get(f"/api/v1/datasets/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "dataset_not_found"


def test_datasets_are_isolated_per_org(app, repos):
    from auth_client.models import IntrospectionResult
    from fastapi.testclient import TestClient

    from dataset_management.api import deps

    org_a, org_b = uuid4(), uuid4()
    app.dependency_overrides[deps.get_dataset_repo] = lambda: repos["dataset"]
    app.dependency_overrides[deps.get_item_repo] = lambda: repos["item"]

    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:a", org_id=str(org_a), scopes=frozenset()
    )
    created = TestClient(app).post("/api/v1/datasets", json={"name": "qa-golden-set"}).json()

    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:b", org_id=str(org_b), scopes=frozenset()
    )
    response = TestClient(app).get(f"/api/v1/datasets/{created['id']}")

    assert response.status_code == 404
    app.dependency_overrides.clear()
