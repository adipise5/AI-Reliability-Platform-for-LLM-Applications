from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, status

from regression_detection.api.deps import (
    get_bearer_credential,
    get_evaluate_run_use_case,
    get_get_gate_decision_use_case,
    org_id_of,
    require_principal,
)
from regression_detection.api.schemas import GateDecisionOut, GateRunIn
from regression_detection.application.evaluate_run import EvaluateRunUseCase
from regression_detection.application.get_gate_decision import GetGateDecisionUseCase

router = APIRouter(prefix="/api/v1/gate-decisions", tags=["gate-decisions"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.post("", response_model=GateDecisionOut, status_code=status.HTTP_201_CREATED)
async def gate_run(
    payload: GateRunIn,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[EvaluateRunUseCase, Depends(get_evaluate_run_use_case)],
) -> GateDecisionOut:
    decision = await use_case.execute(
        org_id=org_id_of(principal), credential=credential, run_id=payload.run_id
    )
    return GateDecisionOut.from_domain(decision)


@router.get("/{run_id}", response_model=GateDecisionOut)
async def get_gate_decision(
    run_id: UUID,
    principal: Principal,
    use_case: Annotated[GetGateDecisionUseCase, Depends(get_get_gate_decision_use_case)],
) -> GateDecisionOut:
    decision = await use_case.execute(org_id=org_id_of(principal), run_id=run_id)
    return GateDecisionOut.from_domain(decision)
