from __future__ import annotations

import pytest

from github_integration.application.handle_webhook import HandleWebhookUseCase
from github_integration.domain.entities import CheckStatus
from github_integration.domain.errors import InvalidWebhookSignatureError
from tests.unit.conftest import (
    FakeCheckRunRepository,
    FakeGitHubClient,
    pull_request_payload,
    signed_payload,
)

SECRET = "s3cr3t"


async def test_raises_on_invalid_signature(org_id):
    repo = FakeCheckRunRepository()
    github = FakeGitHubClient()
    use_case = HandleWebhookUseCase(repo, github, SECRET)
    body, _ = signed_payload(SECRET, pull_request_payload())

    with pytest.raises(InvalidWebhookSignatureError):
        await use_case.execute(
            org_id=org_id, event_type="pull_request", payload_bytes=body, signature_header=None
        )


async def test_creates_a_queued_check_for_opened_pr(org_id):
    repo = FakeCheckRunRepository()
    github = FakeGitHubClient(next_check_run_id=999)
    use_case = HandleWebhookUseCase(repo, github, SECRET)
    body, signature = signed_payload(SECRET, pull_request_payload(action="opened", sha="b" * 40))

    check = await use_case.execute(
        org_id=org_id, event_type="pull_request", payload_bytes=body, signature_header=signature
    )

    assert check is not None
    assert check.status == CheckStatus.QUEUED
    assert check.github_check_run_id == 999
    assert check.commit_sha == "b" * 40
    assert repo.checks[check.id] == check
    assert github.created_checks == [("acme/widgets", "b" * 40, "AI Reliability Gate")]


@pytest.mark.parametrize("action", ["synchronize", "reopened"])
async def test_creates_a_check_for_other_relevant_actions(org_id, action):
    repo = FakeCheckRunRepository()
    github = FakeGitHubClient()
    use_case = HandleWebhookUseCase(repo, github, SECRET)
    body, signature = signed_payload(SECRET, pull_request_payload(action=action))

    check = await use_case.execute(
        org_id=org_id, event_type="pull_request", payload_bytes=body, signature_header=signature
    )

    assert check is not None


async def test_ignores_irrelevant_pull_request_actions(org_id):
    repo = FakeCheckRunRepository()
    github = FakeGitHubClient()
    use_case = HandleWebhookUseCase(repo, github, SECRET)
    body, signature = signed_payload(SECRET, pull_request_payload(action="closed"))

    check = await use_case.execute(
        org_id=org_id, event_type="pull_request", payload_bytes=body, signature_header=signature
    )

    assert check is None
    assert github.created_checks == []


async def test_ignores_non_pull_request_events(org_id):
    repo = FakeCheckRunRepository()
    github = FakeGitHubClient()
    use_case = HandleWebhookUseCase(repo, github, SECRET)
    body, signature = signed_payload(SECRET, {"zen": "keep it simple"})

    check = await use_case.execute(
        org_id=org_id, event_type="ping", payload_bytes=body, signature_header=signature
    )

    assert check is None
    assert github.created_checks == []
