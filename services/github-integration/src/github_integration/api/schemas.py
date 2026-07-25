from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from github_integration.domain.entities import CheckRun


class CompleteCheckIn(BaseModel):
    run_id: UUID


class PostCommentIn(BaseModel):
    pr_number: int = Field(..., gt=0)
    body: str = Field(..., min_length=1)


class CheckRunOut(BaseModel):
    id: UUID
    org_id: UUID
    repo: str
    commit_sha: str
    github_check_run_id: int
    status: str
    conclusion: str | None
    run_id: UUID | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, check: CheckRun) -> CheckRunOut:
        return cls(
            id=check.id,
            org_id=check.org_id,
            repo=check.repo,
            commit_sha=check.commit_sha,
            github_check_run_id=check.github_check_run_id,
            status=check.status.value,
            conclusion=check.conclusion.value if check.conclusion is not None else None,
            run_id=check.run_id,
            created_at=check.created_at,
            completed_at=check.completed_at,
        )


class ErrorOut(BaseModel):
    type: str
    message: str
