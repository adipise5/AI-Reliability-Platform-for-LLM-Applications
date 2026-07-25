from __future__ import annotations

from typing import Annotated

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends

from cost_analytics.api.deps import (
    get_budget_status_use_case,
    get_set_budget_use_case,
    org_id_of,
    require_principal,
)
from cost_analytics.api.schemas import BudgetOut, BudgetStatusOut, SetBudgetIn
from cost_analytics.application.get_budget_status import GetBudgetStatusUseCase
from cost_analytics.application.set_budget import SetBudgetUseCase

router = APIRouter(prefix="/api/v1/budget", tags=["budget"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.put("", response_model=BudgetOut)
async def set_budget(
    payload: SetBudgetIn,
    principal: Principal,
    use_case: Annotated[SetBudgetUseCase, Depends(get_set_budget_use_case)],
) -> BudgetOut:
    budget = await use_case.execute(org_id=org_id_of(principal), monthly_limit_usd=payload.monthly_limit_usd)
    return BudgetOut.from_domain(budget)


@router.get("", response_model=BudgetStatusOut)
async def get_budget_status(
    principal: Principal,
    use_case: Annotated[GetBudgetStatusUseCase, Depends(get_budget_status_use_case)],
) -> BudgetStatusOut:
    budget_status = await use_case.execute(org_id=org_id_of(principal))
    return BudgetStatusOut.from_domain(budget_status)
