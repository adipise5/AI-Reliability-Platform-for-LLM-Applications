from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from github_integration.domain.entities import CheckConclusion, CheckRun, CheckStatus, RemoteGateDecision


class FakeCheckRunRepository:
    def __init__(self, seed: list[CheckRun] | None = None) -> None:
        self.checks: dict[UUID, CheckRun] = {c.id: c for c in (seed or [])}

    async def create(self, check: CheckRun) -> None:
        self.checks[check.id] = check

    async def get_by_id(self, check_id: UUID) -> CheckRun | None:
        return self.checks.get(check_id)

    async def update(self, check: CheckRun) -> None:
        self.checks[check.id] = check

    async def list_by_org(
        self, org_id: UUID, *, repo: str | None = None, commit_sha: str | None = None
    ) -> list[CheckRun]:
        matches = [c for c in self.checks.values() if c.org_id == org_id]
        if repo is not None:
            matches = [c for c in matches if c.repo == repo]
        if commit_sha is not None:
            matches = [c for c in matches if c.commit_sha == commit_sha]
        return sorted(matches, key=lambda c: c.created_at, reverse=True)


class FakeGitHubClient:
    def __init__(self, *, next_check_run_id: int = 555) -> None:
        self._next_check_run_id = next_check_run_id
        self.created_checks: list[tuple[str, str, str]] = []
        self.updated_checks: list[tuple[str, int, CheckStatus, CheckConclusion | None, str]] = []
        self.comments: list[tuple[str, int, str]] = []

    async def create_check_run(self, *, repo: str, commit_sha: str, name: str) -> int:
        self.created_checks.append((repo, commit_sha, name))
        return self._next_check_run_id

    async def update_check_run(
        self,
        *,
        repo: str,
        check_run_id: int,
        status: CheckStatus,
        conclusion: CheckConclusion | None,
        summary: str,
    ) -> None:
        self.updated_checks.append((repo, check_run_id, status, conclusion, summary))

    async def create_pr_comment(self, *, repo: str, pr_number: int, body: str) -> None:
        self.comments.append((repo, pr_number, body))


class FakeGateDecisionReader:
    def __init__(self, decisions: dict[UUID, RemoteGateDecision] | None = None) -> None:
        self.decisions = decisions or {}

    async def get_gate_decision(self, credential: str, run_id: UUID) -> RemoteGateDecision:
        return self.decisions[run_id]


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


def make_check(**overrides: object) -> CheckRun:
    base = CheckRun(
        id=uuid4(),
        org_id=uuid4(),
        repo="acme/widgets",
        commit_sha="a" * 40,
        github_check_run_id=123,
        status=CheckStatus.QUEUED,
        created_at=datetime.now(UTC),
    )
    return replace(base, **overrides)


def make_gate_decision(**overrides: object) -> RemoteGateDecision:
    base = RemoteGateDecision(
        run_id=uuid4(),
        verdict="pass",
        observed_score=0.9,
        baseline_mean=0.85,
        baseline_stddev=0.05,
    )
    return replace(base, **overrides)


def pull_request_payload(*, action: str = "opened", repo: str = "acme/widgets", sha: str = "a" * 40):
    return {
        "action": action,
        "repository": {"full_name": repo},
        "pull_request": {"number": 42, "head": {"sha": sha}},
    }


def signed_payload(secret: str, payload: dict[str, object]) -> tuple[bytes, str]:
    body = json.dumps(payload).encode("utf-8")
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, signature
