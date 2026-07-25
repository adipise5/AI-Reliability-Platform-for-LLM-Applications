from __future__ import annotations

from typing import Annotated

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends

from dashboard_backend.api.deps import (
    get_bearer_credential,
    get_budget_status_use_case,
    get_cost_summary_use_case,
    require_principal,
)
from dashboard_backend.api.schemas import RemoteBudgetStatusOut, RemoteUsageSummaryOut
from dashboard_backend.application.get_budget_status import GetBudgetStatusUseCase
from dashboard_backend.application.get_cost_summary import GetCostSummaryUseCase

router = APIRouter(prefix="/api/v1/cost", tags=["cost"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("/summary", response_model=RemoteUsageSummaryOut)
async def get_cost_summary(
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[GetCostSummaryUseCase, Depends(get_cost_summary_use_case)],
) -> RemoteUsageSummaryOut:
    summary = await use_case.execute(credential=credential)
    return RemoteUsageSummaryOut.from_domain(summary)


@router.get("/budget", response_model=RemoteBudgetStatusOut)
async def get_budget_status(
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[GetBudgetStatusUseCase, Depends(get_budget_status_use_case)],
) -> RemoteBudgetStatusOut:
    status = await use_case.execute(credential=credential)
    return RemoteBudgetStatusOut.from_domain(status)
