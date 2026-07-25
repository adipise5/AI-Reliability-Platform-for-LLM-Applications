from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, status

from hallucination_detection.api.deps import (
    get_bearer_credential,
    get_check_faithfulness_use_case,
    get_get_check_use_case,
    org_id_of,
    require_principal,
)
from hallucination_detection.api.schemas import CheckFaithfulnessIn, FaithfulnessCheckOut
from hallucination_detection.application.check_faithfulness import CheckFaithfulnessUseCase
from hallucination_detection.application.get_check import GetCheckUseCase

router = APIRouter(prefix="/api/v1/faithfulness-checks", tags=["faithfulness-checks"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.post("", response_model=FaithfulnessCheckOut, status_code=status.HTTP_201_CREATED)
async def check_faithfulness(
    payload: CheckFaithfulnessIn,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[CheckFaithfulnessUseCase, Depends(get_check_faithfulness_use_case)],
) -> FaithfulnessCheckOut:
    check = await use_case.execute(
        org_id=org_id_of(principal),
        credential=credential,
        model=payload.model,
        response=payload.response,
        context=payload.context,
    )
    return FaithfulnessCheckOut.from_domain(check)


@router.get("/{check_id}", response_model=FaithfulnessCheckOut)
async def get_check(
    check_id: UUID,
    principal: Principal,
    use_case: Annotated[GetCheckUseCase, Depends(get_get_check_use_case)],
) -> FaithfulnessCheckOut:
    check = await use_case.execute(org_id=org_id_of(principal), check_id=check_id)
    return FaithfulnessCheckOut.from_domain(check)
