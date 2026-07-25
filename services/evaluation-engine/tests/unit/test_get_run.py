from __future__ import annotations

from uuid import uuid4

import pytest

from evaluation_engine.application.get_run import GetEvalRunUseCase
from evaluation_engine.domain.entities import RunItemResult
from evaluation_engine.domain.errors import EvalRunNotFoundError
from tests.unit.conftest import FakeEvalRunRepository, FakeRunItemResultRepository, make_pending_run


async def test_execute_returns_the_run_and_its_items(org_id):
    run = make_pending_run(org_id=org_id)
    item = RunItemResult(
        id=uuid4(), run_id=run.id, dataset_item_id=uuid4(), output="42", latency_ms=1.0,
        prompt_tokens=1, completion_tokens=1,
    )
    item_repo = FakeRunItemResultRepository()
    item_repo.results.append(item)
    use_case = GetEvalRunUseCase(FakeEvalRunRepository(seed=[run]), item_repo)

    fetched_run, items = await use_case.execute(org_id=org_id, run_id=run.id)

    assert fetched_run == run
    assert items == [item]


async def test_execute_rejects_a_run_from_another_org(org_id):
    run = make_pending_run(org_id=org_id)
    use_case = GetEvalRunUseCase(FakeEvalRunRepository(seed=[run]), FakeRunItemResultRepository())

    with pytest.raises(EvalRunNotFoundError):
        await use_case.execute(org_id=uuid4(), run_id=run.id)


async def test_execute_rejects_unknown_run(org_id):
    use_case = GetEvalRunUseCase(FakeEvalRunRepository(), FakeRunItemResultRepository())

    with pytest.raises(EvalRunNotFoundError):
        await use_case.execute(org_id=org_id, run_id=uuid4())
