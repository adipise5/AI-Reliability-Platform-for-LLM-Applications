from __future__ import annotations

from typing import Annotated

from auth_client.models import IntrospectionResult
from fastapi import APIRouter, Depends, Query

from dashboard_backend.api.deps import get_bearer_credential, get_list_checks_use_case, require_principal
from dashboard_backend.api.schemas import RemoteCheckRunOut
from dashboard_backend.application.list_checks import ListChecksUseCase

router = APIRouter(prefix="/api/v1/github", tags=["github"])

Principal = Annotated[IntrospectionResult, Depends(require_principal)]


@router.get("/checks", response_model=list[RemoteCheckRunOut])
async def list_checks(
    principal: Principal,
    credential: Annotated[str, Depends(get_bearer_credential)],
    use_case: Annotated[ListChecksUseCase, Depends(get_list_checks_use_case)],
    repo: str | None = Query(default=None),
    commit_sha: str | None = Query(default=None),
) -> list[RemoteCheckRunOut]:
    checks = await use_case.execute(credential=credential, repo=repo, commit_sha=commit_sha)
    return [RemoteCheckRunOut.from_domain(c) for c in checks]
