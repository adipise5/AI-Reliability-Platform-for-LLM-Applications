"""Ports: interfaces the application layer depends on.

`GitHubClient` talks to GitHub's REST API rather than another bounded
context in this project, but it's still a port for the same reason:
`HandleWebhookUseCase` and `CompleteCheckUseCase` shouldn't know it's
httpx underneath, and a fake makes them testable without a real GitHub
App installation.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from github_integration.domain.entities import CheckConclusion, CheckRun, CheckStatus, RemoteGateDecision


class CheckRunRepository(Protocol):
    async def create(self, check: CheckRun) -> None: ...

    async def get_by_id(self, check_id: UUID) -> CheckRun | None: ...

    async def update(self, check: CheckRun) -> None:
        """Persists the full row — callers read-modify-write via
        `dataclasses.replace`, since `CheckRun` is immutable."""
        ...

    async def list_by_org(
        self, org_id: UUID, *, repo: str | None = None, commit_sha: str | None = None
    ) -> list[CheckRun]:
        """Ordered most-recent-first. `repo`+`commit_sha` is how a CI
        workflow that only knows the commit it's building finds the
        check id the webhook already created for it."""
        ...


class GitHubClient(Protocol):
    async def create_check_run(self, *, repo: str, commit_sha: str, name: str) -> int:
        """Returns GitHub's own check-run id."""
        ...

    async def update_check_run(
        self,
        *,
        repo: str,
        check_run_id: int,
        status: CheckStatus,
        conclusion: CheckConclusion | None,
        summary: str,
    ) -> None: ...

    async def create_pr_comment(self, *, repo: str, pr_number: int, body: str) -> None: ...


class GateDecisionReader(Protocol):
    async def get_gate_decision(self, credential: str, run_id: UUID) -> RemoteGateDecision:
        """Raises `github_integration.domain.errors.UpstreamServiceError`
        if Regression Detection 404s or otherwise fails."""
        ...
