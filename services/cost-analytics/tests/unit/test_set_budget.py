from __future__ import annotations

from cost_analytics.application.set_budget import SetBudgetUseCase
from tests.unit.conftest import FakeBudgetRepository


async def test_execute_creates_a_budget(org_id):
    repo = FakeBudgetRepository()
    use_case = SetBudgetUseCase(repo)

    budget = await use_case.execute(org_id=org_id, monthly_limit_usd=100.0)

    assert repo.budgets[org_id] is budget
    assert budget.monthly_limit_usd == 100.0


async def test_execute_replaces_an_existing_budget_preserving_created_at(org_id):
    repo = FakeBudgetRepository()
    use_case = SetBudgetUseCase(repo)
    first = await use_case.execute(org_id=org_id, monthly_limit_usd=100.0)

    second = await use_case.execute(org_id=org_id, monthly_limit_usd=200.0)

    assert second.id == first.id
    assert second.created_at == first.created_at
    assert second.monthly_limit_usd == 200.0
