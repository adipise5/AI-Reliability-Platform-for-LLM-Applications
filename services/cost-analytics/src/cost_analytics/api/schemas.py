from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from cost_analytics.domain.entities import Budget, BudgetStatus, ModelUsage, UsageSummary


class IngestUsageEventIn(BaseModel):
    org_id: UUID
    provider: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)


class ModelUsageOut(BaseModel):
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float

    @classmethod
    def from_domain(cls, usage: ModelUsage) -> ModelUsageOut:
        return cls(
            provider=usage.provider,
            model=usage.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cost_usd=usage.cost_usd,
        )


class UsageSummaryOut(BaseModel):
    total_cost_usd: float
    total_prompt_tokens: int
    total_completion_tokens: int
    by_model: list[ModelUsageOut]

    @classmethod
    def from_domain(cls, summary: UsageSummary) -> UsageSummaryOut:
        return cls(
            total_cost_usd=summary.total_cost_usd,
            total_prompt_tokens=summary.total_prompt_tokens,
            total_completion_tokens=summary.total_completion_tokens,
            by_model=[ModelUsageOut.from_domain(m) for m in summary.by_model],
        )


class SetBudgetIn(BaseModel):
    monthly_limit_usd: float = Field(..., ge=0)


class BudgetOut(BaseModel):
    org_id: UUID
    monthly_limit_usd: float

    @classmethod
    def from_domain(cls, budget: Budget) -> BudgetOut:
        return cls(org_id=budget.org_id, monthly_limit_usd=budget.monthly_limit_usd)


class BudgetStatusOut(BaseModel):
    spent_this_month_usd: float
    limit_usd: float | None
    remaining_usd: float | None
    over_budget: bool

    @classmethod
    def from_domain(cls, status: BudgetStatus) -> BudgetStatusOut:
        return cls(
            spent_this_month_usd=status.spent_this_month_usd,
            limit_usd=status.limit_usd,
            remaining_usd=status.remaining_usd,
            over_budget=status.over_budget,
        )


class ErrorOut(BaseModel):
    type: str
    message: str
