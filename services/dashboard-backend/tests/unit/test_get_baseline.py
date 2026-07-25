from __future__ import annotations

from uuid import uuid4

from dashboard_backend.application.get_baseline import GetBaselineUseCase
from tests.unit.conftest import FakeRegressionReader, make_baseline


async def test_returns_the_baseline_when_present():
    prompt_id = uuid4()
    baseline = make_baseline(prompt_id=prompt_id)
    use_case = GetBaselineUseCase(FakeRegressionReader(baselines={prompt_id: baseline}))

    result = await use_case.execute(credential="tok", prompt_id=prompt_id)

    assert result == baseline


async def test_returns_none_when_never_gated():
    use_case = GetBaselineUseCase(FakeRegressionReader())

    result = await use_case.execute(credential="tok", prompt_id=uuid4())

    assert result is None
