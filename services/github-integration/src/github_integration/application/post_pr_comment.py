from __future__ import annotations

from uuid import UUID

from github_integration.domain.errors import CheckNotFoundError
from github_integration.domain.ports import CheckRunRepository, GitHubClient


class PostPrCommentUseCase:
    def __init__(self, check_repo: CheckRunRepository, github_client: GitHubClient) -> None:
        self._check_repo = check_repo
        self._github_client = github_client

    async def execute(
        self, *, org_id: UUID, check_id: UUID, pr_number: int, body: str
    ) -> None:
        check = await self._check_repo.get_by_id(check_id)
        if check is None or check.org_id != org_id:
            raise CheckNotFoundError(check_id)

        await self._github_client.create_pr_comment(repo=check.repo, pr_number=pr_number, body=body)
