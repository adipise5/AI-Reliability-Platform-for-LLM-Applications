from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from experiment_tracking.api import deps
from experiment_tracking.api.main import create_app
from experiment_tracking.application.add_run import AddRunUseCase
from experiment_tracking.application.compare_experiment import CompareExperimentUseCase
from experiment_tracking.application.create_experiment import CreateExperimentUseCase
from experiment_tracking.application.get_experiment import GetExperimentUseCase
from experiment_tracking.application.get_score_history import GetScoreHistoryUseCase
from tests.unit.conftest import FakeEvalRunReader, FakeExperimentRepository


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repo():
    return FakeExperimentRepository()


@pytest.fixture
def reader():
    return FakeEvalRunReader()


@pytest.fixture
def client(app, repo, reader, org_id):
    app.dependency_overrides[deps.get_create_experiment_use_case] = lambda: CreateExperimentUseCase(repo)
    app.dependency_overrides[deps.get_add_run_use_case] = lambda: AddRunUseCase(repo, reader)
    app.dependency_overrides[deps.get_get_experiment_use_case] = lambda: GetExperimentUseCase(repo)
    app.dependency_overrides[deps.get_compare_experiment_use_case] = lambda: CompareExperimentUseCase(
        repo, reader
    )
    app.dependency_overrides[deps.get_score_history_use_case] = lambda: GetScoreHistoryUseCase(reader)
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    app.dependency_overrides[deps.get_bearer_credential] = lambda: "fake-bearer-token"
    yield TestClient(app)
    app.dependency_overrides.clear()
