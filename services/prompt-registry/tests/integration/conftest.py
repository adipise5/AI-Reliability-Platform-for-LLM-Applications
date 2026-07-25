from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from prompt_registry.api import deps
from prompt_registry.api.main import create_app
from tests.unit.conftest import FakePromotionRepository, FakePromptRepository, FakePromptVersionRepository


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repos():
    return {
        "prompt": FakePromptRepository(),
        "version": FakePromptVersionRepository(),
        "promotion": FakePromotionRepository(),
    }


@pytest.fixture
def client(app, repos, org_id):
    app.dependency_overrides[deps.get_prompt_repo] = lambda: repos["prompt"]
    app.dependency_overrides[deps.get_version_repo] = lambda: repos["version"]
    app.dependency_overrides[deps.get_promotion_repo] = lambda: repos["promotion"]
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
