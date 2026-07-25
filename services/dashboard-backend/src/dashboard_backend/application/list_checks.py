from __future__ import annotations

from dashboard_backend.domain.entities import RemoteCheckRun
from dashboard_backend.domain.ports import GitHubChecksReader


class ListChecksUseCase:
    def __init__(self, github_checks_reader: GitHubChecksReader) -> None:
        self._github_checks_reader = github_checks_reader

    async def execute(
        self, *, credential: str, repo: str | None = None, commit_sha: str | None = None
    ) -> list[RemoteCheckRun]:
        return await self._github_checks_reader.list_checks(
            credential, repo=repo, commit_sha=commit_sha
        )
