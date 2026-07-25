from __future__ import annotations

from uuid import uuid4

from github_integration.application.list_checks import ListChecksUseCase
from tests.unit.conftest import FakeCheckRunRepository, make_check


async def test_lists_only_checks_for_the_org(org_id):
    mine = make_check(org_id=org_id)
    other = make_check(org_id=uuid4())
    repo = FakeCheckRunRepository([mine, other])
    use_case = ListChecksUseCase(repo)

    checks = await use_case.execute(org_id=org_id)

    assert [c.id for c in checks] == [mine.id]


async def test_filters_by_repo_and_commit_sha(org_id):
    matching = make_check(org_id=org_id, repo="acme/widgets", commit_sha="c" * 40)
    other_repo = make_check(org_id=org_id, repo="acme/other", commit_sha="c" * 40)
    other_sha = make_check(org_id=org_id, repo="acme/widgets", commit_sha="d" * 40)
    repo = FakeCheckRunRepository([matching, other_repo, other_sha])
    use_case = ListChecksUseCase(repo)

    checks = await use_case.execute(org_id=org_id, repo="acme/widgets", commit_sha="c" * 40)

    assert [c.id for c in checks] == [matching.id]
