from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query

from dashboard_backend.api.deps import (
    get_bearer_credential,
    get_get_report_use_case,
    get_list_reports_use_case,
    require_principal,
)
from dashboard_backend.api.schemas import RemoteReportOut
from dashboard_backend.application.get_report import GetReportUseCase
from dashboard_backend.application.list_reports import ListReportsUseCase

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("", response_model=list[RemoteReportOut])
async def list_reports(
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[ListReportsUseCase, Depends(get_list_reports_use_case)],
    experiment_id: UUID | None = Query(default=None),
) -> list[RemoteReportOut]:
    reports = await use_case.execute(credential=credential, experiment_id=experiment_id)
    return [RemoteReportOut.from_domain(r) for r in reports]


@router.get("/{report_id}", response_model=RemoteReportOut)
async def get_report(
    report_id: UUID,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[GetReportUseCase, Depends(get_get_report_use_case)],
) -> RemoteReportOut:
    report = await use_case.execute(credential=credential, report_id=report_id)
    return RemoteReportOut.from_domain(report)
