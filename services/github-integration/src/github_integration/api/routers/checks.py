from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query, status

from github_integration.api.deps import (
    get_bearer_credential,
    get_complete_check_use_case,
    get_get_check_use_case,
    get_list_checks_use_case,
    get_post_pr_comment_use_case,
    org_id_of,
    require_principal,
)
from github_integration.api.schemas import CheckRunOut, CompleteCheckIn, PostCommentIn
from github_integration.application.complete_check import CompleteCheckUseCase
from github_integration.application.get_check import GetCheckUseCase
from github_integration.application.list_checks import ListChecksUseCase
from github_integration.application.post_pr_comment import PostPrCommentUseCase

router = APIRouter(prefix="/api/v1/checks", tags=["checks"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("", response_model=list[CheckRunOut])
async def list_checks(
    principal: Principal,
    use_case: Annotated[ListChecksUseCase, Depends(get_list_checks_use_case)],
    repo: str | None = Query(default=None),
    commit_sha: str | None = Query(default=None),
) -> list[CheckRunOut]:
    checks = await use_case.execute(org_id=org_id_of(principal), repo=repo, commit_sha=commit_sha)
    return [CheckRunOut.from_domain(c) for c in checks]


@router.get("/{check_id}", response_model=CheckRunOut)
async def get_check(
    check_id: UUID,
    principal: Principal,
    use_case: Annotated[GetCheckUseCase, Depends(get_get_check_use_case)],
) -> CheckRunOut:
    check = await use_case.execute(org_id=org_id_of(principal), check_id=check_id)
    return CheckRunOut.from_domain(check)


@router.post("/{check_id}/complete", response_model=CheckRunOut)
async def complete_check(
    check_id: UUID,
    payload: CompleteCheckIn,
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[CompleteCheckUseCase, Depends(get_complete_check_use_case)],
) -> CheckRunOut:
    check = await use_case.execute(
        org_id=org_id_of(principal), credential=credential, check_id=check_id, run_id=payload.run_id
    )
    return CheckRunOut.from_domain(check)


@router.post("/{check_id}/comment", status_code=status.HTTP_204_NO_CONTENT)
async def post_comment(
    check_id: UUID,
    payload: PostCommentIn,
    principal: Principal,
    use_case: Annotated[PostPrCommentUseCase, Depends(get_post_pr_comment_use_case)],
) -> None:
    await use_case.execute(
        org_id=org_id_of(principal), check_id=check_id, pr_number=payload.pr_number, body=payload.body
    )
