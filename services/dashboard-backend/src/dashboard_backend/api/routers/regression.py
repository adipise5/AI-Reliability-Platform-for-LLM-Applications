from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends

from dashboard_backend.api.deps import (
    get_baseline_use_case,
    get_bearer_credential,
    get_latency_anomaly_use_case,
    require_principal,
)
from dashboard_backend.api.schemas import RemoteBaselineOut, RemoteLatencyAnomalyOut
from dashboard_backend.application.get_baseline import GetBaselineUseCase
from dashboard_backend.application.get_latency_anomaly import GetLatencyAnomalyUseCase

router = APIRouter(prefix="/api/v1/regression", tags=["regression"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("/baselines/{prompt_id}", response_model=RemoteBaselineOut | None)
async def get_baseline(
    prompt_id: UUID,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[GetBaselineUseCase, Depends(get_baseline_use_case)],
) -> RemoteBaselineOut | None:
    baseline = await use_case.execute(credential=credential, prompt_id=prompt_id)
    return RemoteBaselineOut.from_domain(baseline) if baseline is not None else None


@router.get("/latency-anomaly", response_model=RemoteLatencyAnomalyOut)
async def get_latency_anomaly(
    principal: Principal,
    use_case: Annotated[GetLatencyAnomalyUseCase, Depends(get_latency_anomaly_use_case)],
) -> RemoteLatencyAnomalyOut:
    anomaly = await use_case.execute()
    return RemoteLatencyAnomalyOut.from_domain(anomaly)
