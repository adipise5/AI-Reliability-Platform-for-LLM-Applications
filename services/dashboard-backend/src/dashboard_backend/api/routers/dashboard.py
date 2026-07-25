from __future__ import annotations

from typing import Annotated

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends

from dashboard_backend.api.deps import (
    get_bearer_credential,
    get_dashboard_overview_use_case,
    require_principal,
)
from dashboard_backend.api.schemas import DashboardOverviewOut
from dashboard_backend.application.get_dashboard_overview import GetDashboardOverviewUseCase

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("/overview", response_model=DashboardOverviewOut)
async def get_overview(
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[GetDashboardOverviewUseCase, Depends(get_dashboard_overview_use_case)],
) -> DashboardOverviewOut:
    overview = await use_case.execute(credential=credential)
    return DashboardOverviewOut.from_domain(overview)
