from __future__ import annotations

from typing import Annotated

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, status

from cost_analytics.api.deps import (
    get_ingest_usage_event_use_case,
    get_usage_summary_use_case,
    org_id_of,
    require_principal,
)
from cost_analytics.api.schemas import IngestUsageEventIn, UsageSummaryOut
from cost_analytics.application.get_usage_summary import GetUsageSummaryUseCase
from cost_analytics.application.ingest_usage_event import IngestUsageEventUseCase

router = APIRouter(prefix="/api/v1", tags=["usage"])


@router.post("/usage-events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_usage_event(
    payload: IngestUsageEventIn,
    use_case: Annotated[IngestUsageEventUseCase, Depends(get_ingest_usage_event_use_case)],
) -> dict[str, str]:
    await use_case.execute(
        org_id=payload.org_id,
        provider=payload.provider,
        model=payload.model,
        prompt_tokens=payload.prompt_tokens,
        completion_tokens=payload.completion_tokens,
    )
    return {"status": "accepted"}


@router.get("/usage", response_model=UsageSummaryOut)
async def get_usage_summary(
    principal: Annotated[IntrospectionResult, Depends(require_principal)],
    use_case: Annotated[GetUsageSummaryUseCase, Depends(get_usage_summary_use_case)],
) -> UsageSummaryOut:
    summary = await use_case.execute(org_id=org_id_of(principal))
    return UsageSummaryOut.from_domain(summary)
