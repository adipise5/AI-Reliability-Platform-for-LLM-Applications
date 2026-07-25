from __future__ import annotations

from uuid import uuid4

import pytest

from regression_detection.application.get_baseline import GetBaselineUseCase
from regression_detection.domain.errors import BaselineNotFoundError
from tests.unit.conftest import FakeBaselineRepository, make_baseline


async def test_returns_the_stored_baseline(org_id):
    prompt_id = uuid4()
    baseline = make_baseline(org_id=org_id, prompt_id=prompt_id)
    repo = FakeBaselineRepository([baseline])
    use_case = GetBaselineUseCase(repo)

    result = await use_case.execute(org_id=org_id, prompt_id=prompt_id)

    assert result.prompt_id == prompt_id


async def test_raises_when_no_baseline_yet(org_id):
    repo = FakeBaselineRepository()
    use_case = GetBaselineUseCase(repo)

    with pytest.raises(BaselineNotFoundError):
        await use_case.execute(org_id=org_id, prompt_id=uuid4())
