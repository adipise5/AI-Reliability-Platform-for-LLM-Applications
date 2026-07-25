from __future__ import annotations

from dashboard_backend.application.get_cost_summary import GetCostSummaryUseCase
from tests.unit.conftest import FakeCostReader, make_usage_summary


async def test_returns_the_usage_summary():
    summary = make_usage_summary(total_cost_usd=42.0)
    use_case = GetCostSummaryUseCase(FakeCostReader(summary=summary))

    result = await use_case.execute(credential="tok")

    assert result == summary
