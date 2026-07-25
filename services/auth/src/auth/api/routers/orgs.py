from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from auth.api.deps import get_register_org_use_case
from auth.api.schemas import RegisterOrgIn, RegisterOrgOut
from auth.application.register_org import RegisterOrgUseCase

router = APIRouter(prefix="/api/v1/orgs", tags=["orgs"])


@router.post("", response_model=RegisterOrgOut, status_code=status.HTTP_201_CREATED)
async def register_org(
    payload: RegisterOrgIn,
    use_case: Annotated[RegisterOrgUseCase, Depends(get_register_org_use_case)],
) -> RegisterOrgOut:
    org, owner = await use_case.execute(
        org_name=payload.org_name,
        owner_email=payload.owner_email,
        owner_password=payload.owner_password,
    )
    return RegisterOrgOut.from_domain(org, owner)
