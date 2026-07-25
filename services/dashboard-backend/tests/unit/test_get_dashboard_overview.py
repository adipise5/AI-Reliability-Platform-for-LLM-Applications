from __future__ import annotations

from dashboard_backend.application.get_dashboard_overview import GetDashboardOverviewUseCase
from dashboard_backend.domain.errors import UpstreamServiceError
from tests.unit.conftest import (
    FakeCostReader,
    FakeEvalRunReader,
    FakeNotificationReader,
    FakeRegressionReader,
    make_notification,
    make_run,
)


def _use_case(**overrides: object) -> GetDashboardOverviewUseCase:
    eval_run_reader = overrides.get("eval_run_reader") or FakeEvalRunReader([make_run()])
    cost_reader = overrides.get("cost_reader") or FakeCostReader()
    regression_reader = overrides.get("regression_reader") or FakeRegressionReader()
    notification_reader = overrides.get("notification_reader") or FakeNotificationReader(
        notifications=[make_notification()]
    )
    return GetDashboardOverviewUseCase(
        eval_run_reader, cost_reader, regression_reader, notification_reader
    )


async def test_merges_all_four_services_when_everything_answers():
    use_case = _use_case()

    overview = await use_case.execute(credential="tok")

    assert len(overview.recent_runs) == 1
    assert overview.cost_summary is not None
    assert overview.budget_status is not None
    assert overview.latency_anomaly is not None
    assert len(overview.recent_notifications) == 1


async def test_degrades_gracefully_when_cost_analytics_is_down():
    use_case = _use_case(
        cost_reader=FakeCostReader(error=UpstreamServiceError("cost-analytics", "timeout"))
    )

    overview = await use_case.execute(credential="tok")

    assert overview.cost_summary is None
    assert overview.budget_status is None
    assert len(overview.recent_runs) == 1  # everything else still populated


async def test_degrades_gracefully_when_regression_detection_is_down():
    use_case = _use_case(
        regression_reader=FakeRegressionReader(
            error=UpstreamServiceError("regression-detection", "timeout")
        )
    )

    overview = await use_case.execute(credential="tok")

    assert overview.latency_anomaly is None


async def test_degrades_gracefully_when_evaluation_engine_is_down():
    use_case = _use_case(
        eval_run_reader=FakeEvalRunReader(error=UpstreamServiceError("evaluation-engine", "timeout"))
    )

    overview = await use_case.execute(credential="tok")

    assert overview.recent_runs == ()


async def test_recent_runs_and_notifications_are_capped_at_ten():
    runs = [make_run() for _ in range(15)]
    notifications = [make_notification() for _ in range(15)]
    use_case = _use_case(
        eval_run_reader=FakeEvalRunReader(runs),
        notification_reader=FakeNotificationReader(notifications=notifications),
    )

    overview = await use_case.execute(credential="tok")

    assert len(overview.recent_runs) == 10
    assert len(overview.recent_notifications) == 10
