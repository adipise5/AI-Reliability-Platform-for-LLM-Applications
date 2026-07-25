"""Use case: the dashboard's home-page snapshot, merged from four
services concurrently via `asyncio.gather` (same concurrency pattern as
the Hallucination Detection service's claim verification).

Deliberately tolerant of partial upstream failure: unlike every other
use case in this project, a failed fetch here doesn't fail the whole
request — it's just missing from the response. A dashboard that shows
recent runs and notifications while cost data happens to be unavailable
is far more useful than a 502 for the whole page; there's no single
business transaction here to keep atomic, only independent reads being
displayed side by side.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable

from dashboard_backend.domain.entities import DashboardOverview
from dashboard_backend.domain.errors import UpstreamServiceError
from dashboard_backend.domain.ports import CostReader, EvalRunReader, NotificationReader, RegressionReader

logger = logging.getLogger(__name__)

_RECENT_RUNS_LIMIT = 10
_RECENT_NOTIFICATIONS_LIMIT = 10


async def _safe[T](awaitable: Awaitable[T], service: str, *, default: T) -> T:
    try:
        return await awaitable
    except UpstreamServiceError:
        logger.warning("dashboard overview: %s did not answer, degrading gracefully", service)
        return default


class GetDashboardOverviewUseCase:
    def __init__(
        self,
        eval_run_reader: EvalRunReader,
        cost_reader: CostReader,
        regression_reader: RegressionReader,
        notification_reader: NotificationReader,
    ) -> None:
        self._eval_run_reader = eval_run_reader
        self._cost_reader = cost_reader
        self._regression_reader = regression_reader
        self._notification_reader = notification_reader

    async def execute(self, *, credential: str) -> DashboardOverview:
        runs, cost_summary, budget_status, latency_anomaly, notifications = await asyncio.gather(
            _safe(self._eval_run_reader.list_runs(credential), "evaluation-engine", default=[]),
            _safe(self._cost_reader.get_usage_summary(credential), "cost-analytics", default=None),
            _safe(self._cost_reader.get_budget_status(credential), "cost-analytics", default=None),
            _safe(self._regression_reader.get_latency_anomaly(), "regression-detection", default=None),
            _safe(
                self._notification_reader.list_notifications(credential),
                "notification-service",
                default=[],
            ),
        )
        return DashboardOverview(
            recent_runs=tuple(runs[:_RECENT_RUNS_LIMIT]),
            cost_summary=cost_summary,
            budget_status=budget_status,
            latency_anomaly=latency_anomaly,
            recent_notifications=tuple(notifications[:_RECENT_NOTIFICATIONS_LIMIT]),
        )
