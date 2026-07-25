from __future__ import annotations

from uuid import uuid4

import pytest

from github_integration.application.complete_check import CompleteCheckUseCase
from github_integration.domain.entities import CheckConclusion, CheckStatus
from github_integration.domain.errors import CheckAlreadyCompletedError, CheckNotFoundError
from tests.unit.conftest import (
    FakeCheckRunRepository,
    FakeGateDecisionReader,
    FakeGitHubClient,
    make_check,
    make_gate_decision,
)


@pytest.mark.parametrize(
    ("verdict", "expected"),
    [
        ("pass", CheckConclusion.SUCCESS),
        ("fail", CheckConclusion.FAILURE),
        ("needs_review", CheckConclusion.NEUTRAL),
    ],
)
async def test_translates_verdict_to_conclusion(org_id, verdict, expected):
    check = make_check(org_id=org_id, status=CheckStatus.QUEUED)
    decision = make_gate_decision(verdict=verdict)
    repo = FakeCheckRunRepository([check])
    github = FakeGitHubClient()
    reader = FakeGateDecisionReader({decision.run_id: decision})
    use_case = CompleteCheckUseCase(repo, reader, github)

    completed = await use_case.execute(
        org_id=org_id, credential="tok", check_id=check.id, run_id=decision.run_id
    )

    assert completed.status == CheckStatus.COMPLETED
    assert completed.conclusion == expected
    assert completed.run_id == decision.run_id
    assert completed.completed_at is not None
    assert github.updated_checks[0][0] == check.repo
    assert github.updated_checks[0][1] == check.github_check_run_id
    assert github.updated_checks[0][3] == expected


async def test_raises_when_check_missing(org_id):
    use_case = CompleteCheckUseCase(
        FakeCheckRunRepository(), FakeGateDecisionReader(), FakeGitHubClient()
    )

    with pytest.raises(CheckNotFoundError):
        await use_case.execute(org_id=org_id, credential="tok", check_id=uuid4(), run_id=uuid4())


async def test_raises_when_check_belongs_to_a_different_org(org_id):
    check = make_check(org_id=uuid4())
    use_case = CompleteCheckUseCase(
        FakeCheckRunRepository([check]), FakeGateDecisionReader(), FakeGitHubClient()
    )

    with pytest.raises(CheckNotFoundError):
        await use_case.execute(org_id=org_id, credential="tok", check_id=check.id, run_id=uuid4())


async def test_raises_when_already_completed(org_id):
    check = make_check(org_id=org_id, status=CheckStatus.COMPLETED)
    use_case = CompleteCheckUseCase(
        FakeCheckRunRepository([check]), FakeGateDecisionReader(), FakeGitHubClient()
    )

    with pytest.raises(CheckAlreadyCompletedError):
        await use_case.execute(org_id=org_id, credential="tok", check_id=check.id, run_id=uuid4())
