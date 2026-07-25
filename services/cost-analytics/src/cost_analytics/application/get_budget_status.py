from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from cost_analytics.domain.entities import BudgetStatus
from cost_analytics.domain.ports import BudgetRepository, UsageRecordRepository


class GetBudgetStatusUseCase:
    def __init__(self, budget_repo: BudgetRepository, usage_repo: UsageRecordRepository) -> None:
        self._budget_repo = budget_repo
        self._usage_repo = usage_repo

    async def execute(self, *, org_id: UUID) -> BudgetStatus:
        budget = await self._budget_repo.get_by_org(org_id)

        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        records_this_month = await self._usage_repo.list_by_org(org_id, since=month_start)
        spent = sum(r.cost_usd for r in records_this_month)

        if budget is None:
            return BudgetStatus(
                spent_this_month_usd=spent, limit_usd=None, remaining_usd=None, over_budget=False
            )

        remaining = budget.monthly_limit_usd - spent
        return BudgetStatus(
            spent_this_month_usd=spent,
            limit_usd=budget.monthly_limit_usd,
            remaining_usd=remaining,
            over_budget=remaining < 0,
        )
