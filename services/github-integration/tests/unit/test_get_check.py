from __future__ import annotations

from uuid import uuid4

import pytest

from github_integration.application.get_check import GetCheckUseCase
from github_integration.domain.errors import CheckNotFoundError
from tests.unit.conftest import FakeCheckRunRepository, make_check


async def test_returns_check_for_the_owning_org(org_id):
    check = make_check(org_id=org_id)
    repo = FakeCheckRunRepository([check])
    use_case = GetCheckUseCase(repo)

    result = await use_case.execute(org_id=org_id, check_id=check.id)

    assert result.id == check.id


async def test_raises_when_missing(org_id):
    repo = FakeCheckRunRepository()
    use_case = GetCheckUseCase(repo)

    with pytest.raises(CheckNotFoundError):
        await use_case.execute(org_id=org_id, check_id=uuid4())


async def test_raises_when_check_belongs_to_a_different_org(org_id):
    check = make_check(org_id=uuid4())
    repo = FakeCheckRunRepository([check])
    use_case = GetCheckUseCase(repo)

    with pytest.raises(CheckNotFoundError):
        await use_case.execute(org_id=org_id, check_id=check.id)
