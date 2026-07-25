from __future__ import annotations

from uuid import UUID

from github_integration.domain.entities import CheckRun
from github_integration.domain.ports import CheckRunRepository


class ListChecksUseCase:
    def __init__(self, check_repo: CheckRunRepository) -> None:
        self._check_repo = check_repo

    async def execute(
        self, *, org_id: UUID, repo: str | None = None, commit_sha: str | None = None
    ) -> list[CheckRun]:
        return await self._check_repo.list_by_org(org_id, repo=repo, commit_sha=commit_sha)
