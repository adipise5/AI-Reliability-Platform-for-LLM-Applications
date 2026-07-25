"""Domain entities for Cost Analytics — see ADR-0001: no framework
imports here.

`org_id` is a `UUID`, matching every other service's convention — the
Gateway sends it as a plain string (see ADR-0006), parsed to `UUID` at the
API boundary (the ingestion schema) so the database column and every
downstream comparison stay typed consistently with the rest of the
platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PricingRate:
    prompt_price_per_1k: float
    completion_price_per_1k: float

    def cost_for(self, *, prompt_tokens: int, completion_tokens: int) -> float:
        return (prompt_tokens / 1000) * self.prompt_price_per_1k + (
            completion_tokens / 1000
        ) * self.completion_price_per_1k


@dataclass(frozen=True, slots=True)
class UsageRecord:
    id: UUID
    org_id: UUID
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, slots=True)
class Budget:
    id: UUID
    org_id: UUID
    monthly_limit_usd: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ModelUsage:
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


@dataclass(frozen=True, slots=True)
class UsageSummary:
    total_cost_usd: float
    total_prompt_tokens: int
    total_completion_tokens: int
    by_model: tuple[ModelUsage, ...]


@dataclass(frozen=True, slots=True)
class BudgetStatus:
    spent_this_month_usd: float
    limit_usd: float | None
    remaining_usd: float | None
    over_budget: bool
