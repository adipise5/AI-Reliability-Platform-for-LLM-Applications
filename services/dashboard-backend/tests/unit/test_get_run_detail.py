from __future__ import annotations

from uuid import uuid4

import pytest

from dashboard_backend.application.get_run_detail import GetRunDetailUseCase
from dashboard_backend.domain.errors import RunNotFoundError
from tests.unit.conftest import (
    FakeEvalRunReader,
    FakeRegressionReader,
    make_gate_decision,
    make_run,
    make_run_item,
)


async def test_merges_run_items_and_gate_decision():
    run = make_run()
    item = make_run_item()
    decision = make_gate_decision(run_id=run.id)
    eval_run_reader = FakeEvalRunReader([run], items_by_run={run.id: (item,)})
    regression_reader = FakeRegressionReader(gate_decisions={run.id: decision})
    use_case = GetRunDetailUseCase(eval_run_reader, regression_reader)

    detail = await use_case.execute(credential="tok", run_id=run.id)

    assert detail.run == run
    assert detail.items == (item,)
    assert detail.gate_decision == decision


async def test_gate_decision_is_none_when_never_gated():
    run = make_run()
    use_case = GetRunDetailUseCase(FakeEvalRunReader([run]), FakeRegressionReader())

    detail = await use_case.execute(credential="tok", run_id=run.id)

    assert detail.gate_decision is None


async def test_raises_when_run_missing():
    use_case = GetRunDetailUseCase(FakeEvalRunReader(), FakeRegressionReader())

    with pytest.raises(RunNotFoundError):
        await use_case.execute(credential="tok", run_id=uuid4())
