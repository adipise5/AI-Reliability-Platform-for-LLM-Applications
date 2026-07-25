"""No auth on this endpoint — it's a stateless read over the Trace
Collector's own open query API (ADR-0004), with no org to scope by yet."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from regression_detection.api.deps import get_check_latency_anomaly_use_case
from regression_detection.api.schemas import LatencyAnomalyOut
from regression_detection.application.check_latency_anomaly import CheckLatencyAnomalyUseCase

router = APIRouter(prefix="/api/v1/latency-anomaly", tags=["latency-anomaly"])


@router.get("", response_model=LatencyAnomalyOut)
async def get_latency_anomaly(
    use_case: Annotated[CheckLatencyAnomalyUseCase, Depends(get_check_latency_anomaly_use_case)],
    limit: int = Query(default=50, ge=1, le=200),
) -> LatencyAnomalyOut:
    check = await use_case.execute(limit=limit)
    return LatencyAnomalyOut.from_domain(check)
