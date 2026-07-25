from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query, status

from evaluation_engine.api.deps import (
    get_bearer_credential,
    get_get_run_use_case,
    get_list_runs_use_case,
    get_trigger_run_use_case,
    org_id_of,
    require_principal,
)
from evaluation_engine.api.schemas import EvalRunDetailOut, EvalRunOut, RunItemResultOut, TriggerRunIn
from evaluation_engine.application.get_run import GetEvalRunUseCase
from evaluation_engine.application.list_runs import ListRunsUseCase
from evaluation_engine.application.trigger_run import TriggerEvalRunUseCase

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.post("", response_model=EvalRunOut, status_code=status.HTTP_202_ACCEPTED)
async def trigger_run(
    payload: TriggerRunIn,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[TriggerEvalRunUseCase, Depends(get_trigger_run_use_case)],
) -> EvalRunOut:
    run = await use_case.execute(
        org_id=org_id_of(principal),
        prompt_id=payload.prompt_id,
        prompt_version_id=payload.prompt_version_id,
        dataset_id=payload.dataset_id,
        model=payload.model,
        credential=credential,
        dataset_version=payload.dataset_version,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        scorer_names=tuple(payload.scorer_names) if payload.scorer_names else None,
    )
    return EvalRunOut.from_domain(run)


@router.get("", response_model=list[EvalRunOut])
async def list_runs(
    principal: Principal,
    use_case: Annotated[ListRunsUseCase, Depends(get_list_runs_use_case)],
    prompt_id: UUID | None = Query(default=None),
    dataset_id: UUID | None = Query(default=None),
) -> list[EvalRunOut]:
    runs = await use_case.execute(
        org_id=org_id_of(principal), prompt_id=prompt_id, dataset_id=dataset_id
    )
    return [EvalRunOut.from_domain(r) for r in runs]


@router.get("/{run_id}", response_model=EvalRunDetailOut)
async def get_run(
    run_id: UUID,
    principal: Principal,
    use_case: Annotated[GetEvalRunUseCase, Depends(get_get_run_use_case)],
) -> EvalRunDetailOut:
    run, items = await use_case.execute(org_id=org_id_of(principal), run_id=run_id)
    return EvalRunDetailOut(
        run=EvalRunOut.from_domain(run), items=[RunItemResultOut.from_domain(i) for i in items]
    )
