from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query, Response, status

from report_generator.api.deps import (
    get_bearer_credential,
    get_get_report_content_use_case,
    get_get_report_use_case,
    get_list_reports_use_case,
    get_request_report_use_case,
    org_id_of,
    require_principal,
)
from report_generator.api.schemas import ReportOut, RequestReportIn
from report_generator.application.get_report import GetReportUseCase
from report_generator.application.get_report_content import GetReportContentUseCase
from report_generator.application.list_reports import ListReportsUseCase
from report_generator.application.request_report import RequestReportUseCase
from report_generator.domain.entities import ReportFormat

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]

_CONTENT_TYPES: dict[ReportFormat, str] = {
    ReportFormat.HTML: "text/html; charset=utf-8",
    ReportFormat.PDF: "application/pdf",
}


@router.post("", response_model=ReportOut, status_code=status.HTTP_202_ACCEPTED)
async def request_report(
    payload: RequestReportIn,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[RequestReportUseCase, Depends(get_request_report_use_case)],
) -> ReportOut:
    report = await use_case.execute(
        org_id=org_id_of(principal),
        experiment_id=payload.experiment_id,
        format=payload.format,
        credential=credential,
    )
    return ReportOut.from_domain(report)


@router.get("", response_model=list[ReportOut])
async def list_reports(
    principal: Principal,
    use_case: Annotated[ListReportsUseCase, Depends(get_list_reports_use_case)],
    experiment_id: UUID | None = Query(default=None),
) -> list[ReportOut]:
    reports = await use_case.execute(org_id=org_id_of(principal), experiment_id=experiment_id)
    return [ReportOut.from_domain(r) for r in reports]


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: UUID,
    principal: Principal,
    use_case: Annotated[GetReportUseCase, Depends(get_get_report_use_case)],
) -> ReportOut:
    report = await use_case.execute(org_id=org_id_of(principal), report_id=report_id)
    return ReportOut.from_domain(report)


@router.get("/{report_id}/content")
async def get_report_content(
    report_id: UUID,
    principal: Principal,
    use_case: Annotated[GetReportContentUseCase, Depends(get_get_report_content_use_case)],
) -> Response:
    report = await use_case.execute(org_id=org_id_of(principal), report_id=report_id)
    assert report.content is not None
    return Response(content=report.content, media_type=_CONTENT_TYPES[report.format])
