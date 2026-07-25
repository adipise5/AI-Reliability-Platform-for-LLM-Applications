"""Requires a principal like every other endpoint here, even though the
Trace Collector itself needs no credential — this BFF is consistently
bearer-authed at its own boundary regardless of what a given upstream
requires."""

from __future__ import annotations

from typing import Annotated

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query

from dashboard_backend.api.deps import get_list_recent_traces_use_case, require_principal
from dashboard_backend.api.schemas import RemoteTraceSummaryOut
from dashboard_backend.application.list_recent_traces import ListRecentTracesUseCase

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("", response_model=list[RemoteTraceSummaryOut])
async def list_recent_traces(
    principal: Principal,
    use_case: Annotated[ListRecentTracesUseCase, Depends(get_list_recent_traces_use_case)],
    limit: int = Query(default=20, ge=1, le=200),
) -> list[RemoteTraceSummaryOut]:
    traces = await use_case.execute(limit=limit)
    return [RemoteTraceSummaryOut.from_domain(t) for t in traces]
