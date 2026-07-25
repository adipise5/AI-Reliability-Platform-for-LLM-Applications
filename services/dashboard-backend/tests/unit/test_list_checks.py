from __future__ import annotations

from dashboard_backend.application.list_checks import ListChecksUseCase
from tests.unit.conftest import FakeGitHubChecksReader, make_check


async def test_filters_by_repo():
    matching = make_check(repo="acme/widgets")
    other = make_check(repo="acme/other")
    use_case = ListChecksUseCase(FakeGitHubChecksReader([matching, other]))

    result = await use_case.execute(credential="tok", repo="acme/widgets")

    assert [c.id for c in result] == [matching.id]
