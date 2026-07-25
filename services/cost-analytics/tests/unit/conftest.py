from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from cost_analytics.domain.entities import Budget, PricingRate, UsageRecord


class FakeUsageRecordRepository:
    def __init__(self, seed: list[UsageRecord] | None = None) -> None:
        self.records: list[UsageRecord] = list(seed or [])

    async def create(self, record: UsageRecord) -> None:
        self.records.append(record)

    async def list_by_org(
        self, org_id: UUID, *, since: datetime | None = None, until: datetime | None = None
    ) -> list[UsageRecord]:
        matches = [r for r in self.records if r.org_id == org_id]
        if since is not None:
            matches = [r for r in matches if r.created_at >= since]
        if until is not None:
            matches = [r for r in matches if r.created_at < until]
        return matches


class FakeBudgetRepository:
    def __init__(self, seed: list[Budget] | None = None) -> None:
        self.budgets: dict[UUID, Budget] = {b.org_id: b for b in (seed or [])}

    async def upsert(self, budget: Budget) -> Budget:
        self.budgets[budget.org_id] = budget
        return budget

    async def get_by_org(self, org_id: UUID) -> Budget | None:
        return self.budgets.get(org_id)


class FakePricingTable:
    def __init__(self, rate: PricingRate | None = None) -> None:
        self._rate = rate if rate is not None else PricingRate(
            prompt_price_per_1k=1.0, completion_price_per_1k=2.0
        )

    def get_rate(self, *, provider: str, model: str) -> PricingRate | None:
        return self._rate


@pytest.fixture
def org_id() -> UUID:
    return uuid4()
