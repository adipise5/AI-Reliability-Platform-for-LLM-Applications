from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends

from regression_detection.api.deps import get_get_baseline_use_case, org_id_of, require_principal
from regression_detection.api.schemas import BaselineOut
from regression_detection.application.get_baseline import GetBaselineUseCase

router = APIRouter(prefix="/api/v1/baselines", tags=["baselines"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("/{prompt_id}", response_model=BaselineOut)
async def get_baseline(
    prompt_id: UUID,
    principal: Principal,
    use_case: Annotated[GetBaselineUseCase, Depends(get_get_baseline_use_case)],
) -> BaselineOut:
    baseline = await use_case.execute(org_id=org_id_of(principal), prompt_id=prompt_id)
    return BaselineOut.from_domain(baseline)
