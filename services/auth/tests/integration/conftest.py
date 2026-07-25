from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from auth.api import deps
from auth.api.main import create_app
from tests.unit.conftest import FakeApiKeyRepository, FakeOrgRepository, FakeUserRepository


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repos():
    return {
        "org": FakeOrgRepository(),
        "user": FakeUserRepository(),
        "api_key": FakeApiKeyRepository(),
    }


@pytest.fixture
def client(app, repos):
    app.dependency_overrides[deps.get_org_repo] = lambda: repos["org"]
    app.dependency_overrides[deps.get_user_repo] = lambda: repos["user"]
    app.dependency_overrides[deps.get_api_key_repo] = lambda: repos["api_key"]
    yield TestClient(app)
    app.dependency_overrides.clear()
