from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from evaluation_engine.application.list_runs import ListRunsUseCase
from tests.unit.conftest import FakeEvalRunRepository, make_pending_run


async def test_execute_returns_runs_for_the_org_only(org_id):
    other_org_run = make_pending_run()
    own_run = make_pending_run(org_id=org_id)
    repo = FakeEvalRunRepository(seed=[other_org_run, own_run])
    use_case = ListRunsUseCase(repo)

    runs = await use_case.execute(org_id=org_id)

    assert runs == [own_run]


async def test_execute_orders_most_recent_first(org_id):
    now = datetime.now(UTC)
    older = make_pending_run(org_id=org_id, created_at=now - timedelta(hours=1))
    newer = make_pending_run(org_id=org_id, created_at=now)
    repo = FakeEvalRunRepository(seed=[older, newer])
    use_case = ListRunsUseCase(repo)

    runs = await use_case.execute(org_id=org_id)

    assert runs == [newer, older]


async def test_execute_filters_by_prompt_id(org_id):
    prompt_id = uuid4()
    matching = make_pending_run(org_id=org_id, prompt_id=prompt_id)
    other = make_pending_run(org_id=org_id)
    repo = FakeEvalRunRepository(seed=[matching, other])
    use_case = ListRunsUseCase(repo)

    runs = await use_case.execute(org_id=org_id, prompt_id=prompt_id)

    assert runs == [matching]


async def test_execute_filters_by_dataset_id(org_id):
    dataset_id = uuid4()
    matching = make_pending_run(org_id=org_id, dataset_id=dataset_id)
    other = make_pending_run(org_id=org_id)
    repo = FakeEvalRunRepository(seed=[matching, other])
    use_case = ListRunsUseCase(repo)

    runs = await use_case.execute(org_id=org_id, dataset_id=dataset_id)

    assert runs == [matching]
