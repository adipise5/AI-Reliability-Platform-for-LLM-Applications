from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query, status

from prompt_registry.api.deps import (
    get_active_version_use_case,
    get_create_prompt_use_case,
    get_create_version_use_case,
    get_diff_versions_use_case,
    get_promote_version_use_case,
    get_version_use_case,
    org_id_of,
    require_principal,
)
from prompt_registry.api.schemas import (
    CreatePromptIn,
    CreateVersionIn,
    PromoteVersionIn,
    PromotionOut,
    PromptOut,
    PromptVersionOut,
    VersionDiffOut,
)
from prompt_registry.application.create_prompt import CreatePromptUseCase
from prompt_registry.application.create_version import CreateVersionUseCase
from prompt_registry.application.diff_versions import DiffVersionsUseCase
from prompt_registry.application.get_active_version import GetActiveVersionUseCase
from prompt_registry.application.get_version import GetVersionUseCase
from prompt_registry.application.promote_version import PromoteVersionUseCase

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.post("", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    payload: CreatePromptIn,
    principal: Principal,
    use_case: Annotated[CreatePromptUseCase, Depends(get_create_prompt_use_case)],
) -> PromptOut:
    prompt = await use_case.execute(org_id=org_id_of(principal), name=payload.name)
    return PromptOut.from_domain(prompt)


@router.post(
    "/{prompt_id}/versions", response_model=PromptVersionOut, status_code=status.HTTP_201_CREATED
)
async def create_version(
    prompt_id: UUID,
    payload: CreateVersionIn,
    principal: Principal,
    use_case: Annotated[CreateVersionUseCase, Depends(get_create_version_use_case)],
) -> PromptVersionOut:
    version = await use_case.execute(
        org_id=org_id_of(principal),
        prompt_id=prompt_id,
        template=payload.template,
        variables_schema=payload.variables_schema,
        semver_tag=payload.semver_tag,
    )
    return PromptVersionOut.from_domain(version)


@router.post(
    "/{prompt_id}/promotions", response_model=PromotionOut, status_code=status.HTTP_201_CREATED
)
async def promote_version(
    prompt_id: UUID,
    payload: PromoteVersionIn,
    principal: Principal,
    use_case: Annotated[PromoteVersionUseCase, Depends(get_promote_version_use_case)],
) -> PromotionOut:
    event = await use_case.execute(
        org_id=org_id_of(principal),
        prompt_id=prompt_id,
        version_id=payload.version_id,
        environment=payload.environment,
    )
    return PromotionOut.from_domain(event)


@router.get("/{prompt_id}/versions/active", response_model=PromptVersionOut)
async def get_active_version(
    prompt_id: UUID,
    principal: Principal,
    use_case: Annotated[GetActiveVersionUseCase, Depends(get_active_version_use_case)],
    environment: str = Query(..., min_length=1, max_length=50),
) -> PromptVersionOut:
    version = await use_case.execute(
        org_id=org_id_of(principal), prompt_id=prompt_id, environment=environment
    )
    return PromptVersionOut.from_domain(version)


@router.get("/{prompt_id}/versions/diff", response_model=VersionDiffOut)
async def diff_versions(
    prompt_id: UUID,
    principal: Principal,
    use_case: Annotated[DiffVersionsUseCase, Depends(get_diff_versions_use_case)],
    a: UUID = Query(...),
    b: UUID = Query(...),
) -> VersionDiffOut:
    diff = await use_case.execute(
        org_id=org_id_of(principal), prompt_id=prompt_id, version_a_id=a, version_b_id=b
    )
    return VersionDiffOut.from_domain(diff)


# Registered after the /versions/active and /versions/diff literal routes,
# deliberately: Starlette matches path routes in registration order, so a
# dynamic /versions/{version_id} registered first would swallow both of
# those literal paths as version_id="active" / "diff".
@router.get("/{prompt_id}/versions/{version_id}", response_model=PromptVersionOut)
async def get_version(
    prompt_id: UUID,
    version_id: UUID,
    principal: Principal,
    use_case: Annotated[GetVersionUseCase, Depends(get_version_use_case)],
) -> PromptVersionOut:
    version = await use_case.execute(
        org_id=org_id_of(principal), prompt_id=prompt_id, version_id=version_id
    )
    return PromptVersionOut.from_domain(version)
