from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from cost_analytics.domain.entities import Budget
from cost_analytics.domain.ports import BudgetRepository


class SetBudgetUseCase:
    """Upserts — one budget per org, so "set" always means "replace
    whatever was there," not "create, and error if one exists."""

    def __init__(self, budget_repo: BudgetRepository) -> None:
        self._budget_repo = budget_repo

    async def execute(self, *, org_id: UUID, monthly_limit_usd: float) -> Budget:
        existing = await self._budget_repo.get_by_org(org_id)
        now = datetime.now(UTC)
        budget = Budget(
            id=existing.id if existing else uuid4(),
            org_id=org_id,
            monthly_limit_usd=monthly_limit_usd,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        return await self._budget_repo.upsert(budget)
