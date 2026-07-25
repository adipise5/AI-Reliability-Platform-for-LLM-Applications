from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from hallucination_detection.application.get_check import GetCheckUseCase
from hallucination_detection.domain.entities import FaithfulnessCheck
from hallucination_detection.domain.errors import FaithfulnessCheckNotFoundError
from tests.unit.conftest import FakeFaithfulnessCheckRepository


def _make_check(org_id) -> FaithfulnessCheck:
    return FaithfulnessCheck(
        id=uuid4(), org_id=org_id, response="r", context="c", created_at=datetime.now(UTC)
    )


async def test_execute_returns_an_owned_check(org_id):
    check = _make_check(org_id)
    use_case = GetCheckUseCase(FakeFaithfulnessCheckRepository(seed=[check]))

    result = await use_case.execute(org_id=org_id, check_id=check.id)

    assert result == check


async def test_execute_rejects_a_check_from_another_org(org_id):
    check = _make_check(org_id)
    use_case = GetCheckUseCase(FakeFaithfulnessCheckRepository(seed=[check]))

    with pytest.raises(FaithfulnessCheckNotFoundError):
        await use_case.execute(org_id=uuid4(), check_id=check.id)


async def test_execute_rejects_unknown_check(org_id):
    use_case = GetCheckUseCase(FakeFaithfulnessCheckRepository())

    with pytest.raises(FaithfulnessCheckNotFoundError):
        await use_case.execute(org_id=org_id, check_id=uuid4())
