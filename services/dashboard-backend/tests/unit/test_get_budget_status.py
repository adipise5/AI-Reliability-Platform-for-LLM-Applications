from __future__ import annotations

from dashboard_backend.application.get_budget_status import GetBudgetStatusUseCase
from tests.unit.conftest import FakeCostReader, make_budget_status


async def test_returns_the_budget_status():
    budget = make_budget_status(over_budget=True)
    use_case = GetBudgetStatusUseCase(FakeCostReader(budget=budget))

    result = await use_case.execute(credential="tok")

    assert result == budget
