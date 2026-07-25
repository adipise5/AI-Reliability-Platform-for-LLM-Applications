from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends

from dashboard_backend.api.deps import (
    get_bearer_credential,
    get_list_runs_use_case,
    get_run_detail_use_case,
    require_principal,
)
from dashboard_backend.api.schemas import RemoteEvalRunOut, RunDetailOut
from dashboard_backend.application.get_run_detail import GetRunDetailUseCase
from dashboard_backend.application.list_runs import ListRunsUseCase

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("", response_model=list[RemoteEvalRunOut])
async def list_runs(
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[ListRunsUseCase, Depends(get_list_runs_use_case)],
) -> list[RemoteEvalRunOut]:
    runs = await use_case.execute(credential=credential)
    return [RemoteEvalRunOut.from_domain(r) for r in runs]


@router.get("/{run_id}", response_model=RunDetailOut)
async def get_run_detail(
    run_id: UUID,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[GetRunDetailUseCase, Depends(get_run_detail_use_case)],
) -> RunDetailOut:
    detail = await use_case.execute(credential=credential, run_id=run_id)
    return RunDetailOut.from_domain(detail)
