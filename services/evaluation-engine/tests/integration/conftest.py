from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from evaluation_engine.api import deps
from evaluation_engine.api.main import create_app
from evaluation_engine.application.get_run import GetEvalRunUseCase
from evaluation_engine.application.list_runs import ListRunsUseCase
from evaluation_engine.application.trigger_run import TriggerEvalRunUseCase
from tests.unit.conftest import FakeEvalRunRepository, FakeRunItemResultRepository, FakeTaskQueue


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repos():
    return {"run": FakeEvalRunRepository(), "item": FakeRunItemResultRepository(), "queue": FakeTaskQueue()}


@pytest.fixture
def client(app, repos, org_id):
    app.dependency_overrides[deps.get_trigger_run_use_case] = lambda: TriggerEvalRunUseCase(
        repos["run"], repos["queue"]
    )
    app.dependency_overrides[deps.get_get_run_use_case] = lambda: GetEvalRunUseCase(
        repos["run"], repos["item"]
    )
    app.dependency_overrides[deps.get_list_runs_use_case] = lambda: ListRunsUseCase(repos["run"])
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    app.dependency_overrides[deps.get_bearer_credential] = lambda: "fake-bearer-token"
    yield TestClient(app)
    app.dependency_overrides.clear()
