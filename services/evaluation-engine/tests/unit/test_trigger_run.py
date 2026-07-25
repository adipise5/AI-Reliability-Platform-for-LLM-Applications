from __future__ import annotations

from uuid import uuid4

from evaluation_engine.application.trigger_run import DEFAULT_SCORERS, TriggerEvalRunUseCase
from evaluation_engine.domain.entities import RunStatus
from tests.unit.conftest import FakeEvalRunRepository, FakeTaskQueue


async def test_execute_creates_a_pending_run_and_enqueues_it(org_id):
    repo = FakeEvalRunRepository()
    queue = FakeTaskQueue()
    use_case = TriggerEvalRunUseCase(repo, queue)
    prompt_id, version_id, dataset_id = uuid4(), uuid4(), uuid4()

    run = await use_case.execute(
        org_id=org_id,
        prompt_id=prompt_id,
        prompt_version_id=version_id,
        dataset_id=dataset_id,
        model="claude-sonnet-5",
        credential="tok-123",
    )

    assert repo.runs[run.id] is run
    assert run.status == RunStatus.PENDING
    assert run.scorer_names == DEFAULT_SCORERS
    assert queue.enqueued == [(run.id, "tok-123")]


async def test_execute_honors_explicit_scorer_names(org_id):
    use_case = TriggerEvalRunUseCase(FakeEvalRunRepository(), FakeTaskQueue())

    run = await use_case.execute(
        org_id=org_id,
        prompt_id=uuid4(),
        prompt_version_id=uuid4(),
        dataset_id=uuid4(),
        model="claude-sonnet-5",
        credential="tok",
        scorer_names=("exact_match", "llm_judge"),
    )

    assert run.scorer_names == ("exact_match", "llm_judge")


async def test_execute_pins_an_explicit_dataset_version(org_id):
    use_case = TriggerEvalRunUseCase(FakeEvalRunRepository(), FakeTaskQueue())

    run = await use_case.execute(
        org_id=org_id,
        prompt_id=uuid4(),
        prompt_version_id=uuid4(),
        dataset_id=uuid4(),
        model="claude-sonnet-5",
        credential="tok",
        dataset_version=3,
    )

    assert run.dataset_version == 3
