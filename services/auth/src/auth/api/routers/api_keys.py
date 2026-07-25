from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from auth.api.deps import get_create_api_key_use_case, get_revoke_api_key_use_case, require_org_admin
from auth.api.schemas import CreateApiKeyIn, CreateApiKeyOut
from auth.application.create_api_key import CreateApiKeyUseCase
from auth.application.revoke_api_key import RevokeApiKeyUseCase
from auth.domain.entities import Principal

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


@router.post("", response_model=CreateApiKeyOut, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: CreateApiKeyIn,
    principal: Annotated[Principal, Depends(require_org_admin)],
    use_case: Annotated[CreateApiKeyUseCase, Depends(get_create_api_key_use_case)],
) -> CreateApiKeyOut:
    requested = frozenset(payload.scopes) if payload.scopes is not None else None
    api_key, secret = await use_case.execute(
        org_id=principal.org_id,
        name=payload.name,
        creator_scopes=principal.scopes,
        requested_scopes=requested,
    )
    return CreateApiKeyOut.from_domain(api_key, secret)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    principal: Annotated[Principal, Depends(require_org_admin)],
    use_case: Annotated[RevokeApiKeyUseCase, Depends(get_revoke_api_key_use_case)],
) -> None:
    await use_case.execute(org_id=principal.org_id, key_id=key_id)
