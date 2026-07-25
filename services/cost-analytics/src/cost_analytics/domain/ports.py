from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from cost_analytics.domain.entities import Budget, PricingRate, UsageRecord


class UsageRecordRepository(Protocol):
    async def create(self, record: UsageRecord) -> None: ...

    async def list_by_org(
        self, org_id: UUID, *, since: datetime | None = None, until: datetime | None = None
    ) -> list[UsageRecord]:
        """`since`/`until` bound the query — `GetBudgetStatusUseCase` uses
        them to sum only this calendar month's spend."""
        ...


class BudgetRepository(Protocol):
    async def upsert(self, budget: Budget) -> Budget: ...

    async def get_by_org(self, org_id: UUID) -> Budget | None: ...


class PricingTable(Protocol):
    def get_rate(self, *, provider: str, model: str) -> PricingRate | None:
        """`None` means "no rate on file" — callers treat that as zero
        cost rather than failing the whole ingestion, since an unpriced
        model shouldn't block usage tracking for every priced one."""
        ...
