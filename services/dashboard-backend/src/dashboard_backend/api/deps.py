"""Dependency wiring — see the gateway's api/deps.py for the rationale.

No database session here at all — see `infrastructure/config.py`'s
docstring: this is the one service in the catalog with nothing of its
own to persist, only a bearer credential to forward to whichever
read-facing service a given endpoint fans out to.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from auth_client import AuthServiceClient
from auth_client.fastapi import RequirePrincipal
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
from dashboard_backend.domain.ports import (
    CostReader,
    EvalRunReader,
    GitHubChecksReader,
    NotificationReader,
    RegressionReader,
    ReportReader,
    TraceReader,
)
from dashboard_backend.infrastructure.clients.cost_analytics_client import HttpCostReader
from dashboard_backend.infrastructure.clients.evaluation_engine_client import HttpEvalRunReader
from dashboard_backend.infrastructure.clients.github_integration_client import HttpGitHubChecksReader
from dashboard_backend.infrastructure.clients.notification_client import HttpNotificationReader
from dashboard_backend.infrastructure.clients.regression_detection_client import HttpRegressionReader
from dashboard_backend.infrastructure.clients.report_generator_client import HttpReportReader
from dashboard_backend.infrastructure.clients.trace_collector_client import HttpTraceReader
from dashboard_backend.infrastructure.config import get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _eval_run_reader() -> EvalRunReader:
    settings = get_settings()
    return HttpEvalRunReader(settings.evaluation_engine_url, timeout=settings.upstream_timeout_seconds)


@lru_cache
def _cost_reader() -> CostReader:
    settings = get_settings()
    return HttpCostReader(settings.cost_analytics_url, timeout=settings.upstream_timeout_seconds)


@lru_cache
def _regression_reader() -> RegressionReader:
    settings = get_settings()
    return HttpRegressionReader(
        settings.regression_detection_url, timeout=settings.upstream_timeout_seconds
    )


@lru_cache
def _report_reader() -> ReportReader:
    settings = get_settings()
    return HttpReportReader(settings.report_generator_url, timeout=settings.upstream_timeout_seconds)


@lru_cache
def _notification_reader() -> NotificationReader:
    settings = get_settings()
    return HttpNotificationReader(
        settings.notification_service_url, timeout=settings.upstream_timeout_seconds
    )


@lru_cache
def _github_checks_reader() -> GitHubChecksReader:
    settings = get_settings()
    return HttpGitHubChecksReader(
        settings.github_integration_url, timeout=settings.upstream_timeout_seconds
    )


@lru_cache
def _trace_reader() -> TraceReader:
    settings = get_settings()
    return HttpTraceReader(settings.trace_collector_url, timeout=settings.upstream_timeout_seconds)


def get_dashboard_overview_use_case() -> GetDashboardOverviewUseCase:
    return GetDashboardOverviewUseCase(
        _eval_run_reader(), _cost_reader(), _regression_reader(), _notification_reader()
    )


def get_list_runs_use_case() -> ListRunsUseCase:
    return ListRunsUseCase(_eval_run_reader())


def get_run_detail_use_case() -> GetRunDetailUseCase:
    return GetRunDetailUseCase(_eval_run_reader(), _regression_reader())


def get_cost_summary_use_case() -> GetCostSummaryUseCase:
    return GetCostSummaryUseCase(_cost_reader())


def get_budget_status_use_case() -> GetBudgetStatusUseCase:
    return GetBudgetStatusUseCase(_cost_reader())


def get_baseline_use_case() -> GetBaselineUseCase:
    return GetBaselineUseCase(_regression_reader())


def get_latency_anomaly_use_case() -> GetLatencyAnomalyUseCase:
    return GetLatencyAnomalyUseCase(_regression_reader())


def get_list_reports_use_case() -> ListReportsUseCase:
    return ListReportsUseCase(_report_reader())


def get_get_report_use_case() -> GetReportUseCase:
    return GetReportUseCase(_report_reader())


def get_list_channels_use_case() -> ListChannelsUseCase:
    return ListChannelsUseCase(_notification_reader())


def get_list_notifications_use_case() -> ListNotificationsUseCase:
    return ListNotificationsUseCase(_notification_reader())


def get_list_checks_use_case() -> ListChecksUseCase:
    return ListChecksUseCase(_github_checks_reader())


def get_list_recent_traces_use_case() -> ListRecentTracesUseCase:
    return ListRecentTracesUseCase(_trace_reader())


@lru_cache
def _auth_client() -> AuthServiceClient:
    settings = get_settings()
    return AuthServiceClient(settings.auth_service_url, timeout=settings.upstream_timeout_seconds)


require_principal = RequirePrincipal(_auth_client())


async def get_bearer_credential(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> str:
    assert credentials is not None
    return credentials.credentials


def reset_cached_singletons() -> None:
    """Test-only hook — see the gateway's equivalent for why."""
    get_settings.cache_clear()
    _eval_run_reader.cache_clear()
    _cost_reader.cache_clear()
    _regression_reader.cache_clear()
    _report_reader.cache_clear()
    _notification_reader.cache_clear()
    _github_checks_reader.cache_clear()
    _trace_reader.cache_clear()
    _auth_client.cache_clear()
