from __future__ import annotations

from uuid import uuid4

import pytest
from auth_client.models import IntrospectionResult
from fastapi.testclient import TestClient

from dashboard_backend.api import deps
from dashboard_backend.api.main import create_app
from dashboard_backend.application.get_baseline import GetBaselineUseCase
from dashboard_backend.application.get_budget_status import GetBudgetStatusUseCase
from dashboard_backend.application.get_cost_summary import GetCostSummaryUseCase
from dashboard_backend.application.get_dashboard_overview import GetDashboardOverviewUseCase
from dashboard_backend.application.get_latency_anomaly import GetLatencyAnomalyUseCase
from dashboard_backend.application.get_report import GetReportUseCase
from dashboard_backend.application.get_run_detail import GetRunDetailUseCase
from dashboard_backend.application.list_channels import ListChannelsUseCase
from dashboard_backend.application.list_checks import ListChecksUseCase
from dashboard_backend.application.list_notifications import ListNotificationsUseCase
from dashboard_backend.application.list_recent_traces import ListRecentTracesUseCase
from dashboard_backend.application.list_reports import ListReportsUseCase
from dashboard_backend.application.list_runs import ListRunsUseCase
from tests.unit.conftest import (
    FakeCostReader,
    FakeEvalRunReader,
    FakeGitHubChecksReader,
    FakeNotificationReader,
    FakeRegressionReader,
    FakeReportReader,
    FakeTraceReader,
)


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def eval_run_reader():
    return FakeEvalRunReader()


@pytest.fixture
def cost_reader():
    return FakeCostReader()


@pytest.fixture
def regression_reader():
    return FakeRegressionReader()


@pytest.fixture
def report_reader():
    return FakeReportReader()


@pytest.fixture
def notification_reader():
    return FakeNotificationReader()


@pytest.fixture
def github_checks_reader():
    return FakeGitHubChecksReader()


@pytest.fixture
def trace_reader():
    return FakeTraceReader()


@pytest.fixture
def client(
    app,
    eval_run_reader,
    cost_reader,
    regression_reader,
    report_reader,
    notification_reader,
    github_checks_reader,
    trace_reader,
    org_id,
):
    app.dependency_overrides[deps.get_dashboard_overview_use_case] = lambda: GetDashboardOverviewUseCase(
        eval_run_reader, cost_reader, regression_reader, notification_reader
    )
    app.dependency_overrides[deps.get_list_runs_use_case] = lambda: ListRunsUseCase(eval_run_reader)
    app.dependency_overrides[deps.get_run_detail_use_case] = lambda: GetRunDetailUseCase(
        eval_run_reader, regression_reader
    )
    app.dependency_overrides[deps.get_cost_summary_use_case] = lambda: GetCostSummaryUseCase(cost_reader)
    app.dependency_overrides[deps.get_budget_status_use_case] = lambda: GetBudgetStatusUseCase(
        cost_reader
    )
    app.dependency_overrides[deps.get_baseline_use_case] = lambda: GetBaselineUseCase(regression_reader)
    app.dependency_overrides[deps.get_latency_anomaly_use_case] = lambda: GetLatencyAnomalyUseCase(
        regression_reader
    )
    app.dependency_overrides[deps.get_list_reports_use_case] = lambda: ListReportsUseCase(report_reader)
    app.dependency_overrides[deps.get_get_report_use_case] = lambda: GetReportUseCase(report_reader)
    app.dependency_overrides[deps.get_list_channels_use_case] = lambda: ListChannelsUseCase(
        notification_reader
    )
    app.dependency_overrides[deps.get_list_notifications_use_case] = lambda: ListNotificationsUseCase(
        notification_reader
    )
    app.dependency_overrides[deps.get_list_checks_use_case] = lambda: ListChecksUseCase(
        github_checks_reader
    )
    app.dependency_overrides[deps.get_list_recent_traces_use_case] = lambda: ListRecentTracesUseCase(
        trace_reader
    )
    app.dependency_overrides[deps.require_principal] = lambda: IntrospectionResult(
        subject="user:test", org_id=str(org_id), scopes=frozenset({"chat:write"})
    )
    app.dependency_overrides[deps.get_bearer_credential] = lambda: "fake-bearer-token"
    yield TestClient(app)
    app.dependency_overrides.clear()
