from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from dataset_management.api import deps
from dataset_management.api.main import create_app
from tests.unit.conftest import FakeDatasetItemRepository, FakeDatasetRepository


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repos():
    return {"dataset": FakeDatasetRepository(), "item": FakeDatasetItemRepository()}


@pytest.fixture
def client(app, repos, org_id):
    app.dependency_overrides[deps.get_dataset_repo] = lambda: repos["dataset"]
    app.dependency_overrides[deps.get_item_repo] = lambda: repos["item"]
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
