from __future__ import annotations

from uuid import uuid4

import pytest

from github_integration.application.post_pr_comment import PostPrCommentUseCase
from github_integration.domain.errors import CheckNotFoundError
from tests.unit.conftest import FakeCheckRunRepository, FakeGitHubClient, make_check


async def test_posts_a_comment_on_the_checks_repo(org_id):
    check = make_check(org_id=org_id, repo="acme/widgets")
    repo = FakeCheckRunRepository([check])
    github = FakeGitHubClient()
    use_case = PostPrCommentUseCase(repo, github)

    await use_case.execute(org_id=org_id, check_id=check.id, pr_number=42, body="hello")

    assert github.comments == [("acme/widgets", 42, "hello")]


async def test_raises_when_check_missing(org_id):
    use_case = PostPrCommentUseCase(FakeCheckRunRepository(), FakeGitHubClient())

    with pytest.raises(CheckNotFoundError):
        await use_case.execute(org_id=org_id, check_id=uuid4(), pr_number=1, body="x")


async def test_raises_when_check_belongs_to_a_different_org(org_id):
    check = make_check(org_id=uuid4())
    use_case = PostPrCommentUseCase(FakeCheckRunRepository([check]), FakeGitHubClient())

    with pytest.raises(CheckNotFoundError):
        await use_case.execute(org_id=org_id, check_id=check.id, pr_number=1, body="x")
