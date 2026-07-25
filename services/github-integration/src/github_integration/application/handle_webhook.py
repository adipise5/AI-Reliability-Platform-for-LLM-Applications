"""Use case: react to a GitHub webhook delivery.

Only `pull_request` events with action `opened`, `synchronize`, or
`reopened` do anything — everything else is acknowledged (200) and
ignored, since there's no check to create or update for it yet. Creating
the check here, in `queued` state, before any eval run exists is
deliberate: it's the fastest possible feedback to a PR ("the gate is
running") and gives the CI workflow a `(repo, commit_sha)` pair it can
use via `ListChecksUseCase` to find this check's id once its own eval run
finishes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from github_integration.domain.entities import CheckRun, CheckStatus
from github_integration.domain.errors import InvalidWebhookSignatureError
from github_integration.domain.ports import CheckRunRepository, GitHubClient
from github_integration.domain.webhook_signature import verify_signature

_RELEVANT_ACTIONS = {"opened", "synchronize", "reopened"}


class HandleWebhookUseCase:
    def __init__(
        self, check_repo: CheckRunRepository, github_client: GitHubClient, webhook_secret: str
    ) -> None:
        self._check_repo = check_repo
        self._github_client = github_client
        self._webhook_secret = webhook_secret

    async def execute(
        self,
        *,
        org_id: UUID,
        event_type: str,
        payload_bytes: bytes,
        signature_header: str | None,
    ) -> CheckRun | None:
        if not verify_signature(self._webhook_secret, payload_bytes, signature_header):
            raise InvalidWebhookSignatureError

        if event_type != "pull_request":
            return None

        payload: dict[str, Any] = json.loads(payload_bytes)
        if payload.get("action") not in _RELEVANT_ACTIONS:
            return None

        repo = str(payload["repository"]["full_name"])
        commit_sha = str(payload["pull_request"]["head"]["sha"])

        github_check_run_id = await self._github_client.create_check_run(
            repo=repo, commit_sha=commit_sha, name="AI Reliability Gate"
        )

        check = CheckRun(
            id=uuid4(),
            org_id=org_id,
            repo=repo,
            commit_sha=commit_sha,
            github_check_run_id=github_check_run_id,
            status=CheckStatus.QUEUED,
            created_at=datetime.now(UTC),
        )
        await self._check_repo.create(check)
        return check
