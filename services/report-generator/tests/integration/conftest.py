from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from report_generator.api import deps
from report_generator.api.main import create_app
from report_generator.application.get_report import GetReportUseCase
from report_generator.application.get_report_content import GetReportContentUseCase
from report_generator.application.list_reports import ListReportsUseCase
from report_generator.application.request_report import RequestReportUseCase
from tests.unit.conftest import FakeReportRepository, FakeTaskQueue


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def repo():
    return FakeReportRepository()


@pytest.fixture
def queue():
    return FakeTaskQueue()


@pytest.fixture
def client(app, repo, queue, org_id):
    app.dependency_overrides[deps.get_request_report_use_case] = lambda: RequestReportUseCase(
        repo, queue
    )
    app.dependency_overrides[deps.get_get_report_use_case] = lambda: GetReportUseCase(repo)
    app.dependency_overrides[deps.get_list_reports_use_case] = lambda: ListReportsUseCase(repo)
    app.dependency_overrides[deps.get_get_report_content_use_case] = lambda: GetReportContentUseCase(
        repo
    )
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    app.dependency_overrides[deps.get_bearer_credential] = lambda: "fake-bearer-token"
    yield TestClient(app)
    app.dependency_overrides.clear()
