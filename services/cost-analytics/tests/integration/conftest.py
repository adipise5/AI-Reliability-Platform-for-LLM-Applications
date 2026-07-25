from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from cost_analytics.api import deps
from cost_analytics.api.main import create_app
from tests.unit.conftest import FakeBudgetRepository, FakePricingTable, FakeUsageRecordRepository


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repos():
    return {
        "usage": FakeUsageRecordRepository(),
        "budget": FakeBudgetRepository(),
        "pricing": FakePricingTable(),
    }


@pytest.fixture
def client(app, repos, org_id):
    app.dependency_overrides[deps.get_usage_repo] = lambda: repos["usage"]
    app.dependency_overrides[deps.get_budget_repo] = lambda: repos["budget"]
    app.dependency_overrides[deps.get_pricing_table] = lambda: repos["pricing"]
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
