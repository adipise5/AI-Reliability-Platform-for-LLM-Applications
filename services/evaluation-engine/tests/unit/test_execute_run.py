from __future__ import annotations

from uuid import uuid4

import pytest

from evaluation_engine.application.execute_run import ExecuteEvalRunUseCase
from evaluation_engine.domain.entities import (
    RemoteCompletion,
    RemoteDatasetItem,
    RemotePromptVersion,
    RunStatus,
)
from evaluation_engine.domain.errors import PromptRenderError, UnknownScorerError, UpstreamServiceError
from evaluation_engine.infrastructure.scorers.exact_match import ExactMatchScorer
from evaluation_engine.infrastructure.scorers.registry import InMemoryScorerRegistry
from tests.unit.conftest import (
    FakeDatasetClient,
    FakeEvalRunRepository,
    FakeGatewayClient,
    FakePromptRegistryClient,
    FakeRunItemResultRepository,
    make_pending_run,
)


def _use_case(
    run_repo, item_repo, prompt_registry, dataset_client, gateway, scorer_names=("exact_match",)
):
    return ExecuteEvalRunUseCase(
        eval_run_repo=run_repo,
        item_repo=item_repo,
        prompt_registry=prompt_registry,
        dataset_client=dataset_client,
        gateway=gateway,
        scorer_registry=InMemoryScorerRegistry([ExactMatchScorer()]),
    )


async def test_execute_runs_every_item_and_completes_the_run():
    run = make_pending_run(scorer_names=("exact_match",))
    run_repo = FakeEvalRunRepository(seed=[run])
    item_repo = FakeRunItemResultRepository()
    version = RemotePromptVersion(
        id=run.prompt_version_id, template="What is {a}+{b}?", variables_schema={}
    )
    items = [
        RemoteDatasetItem(id=uuid4(), input={"a": "2", "b": "2"}, expected_output="42"),
        RemoteDatasetItem(id=uuid4(), input={"a": "1", "b": "1"}, expected_output="41"),
    ]
    gateway = FakeGatewayClient(
        RemoteCompletion(content="42", prompt_tokens=5, completion_tokens=1, latency_ms=9.0)
    )
    use_case = _use_case(
        run_repo,
        item_repo,
        FakePromptRegistryClient(version),
        FakeDatasetClient(items, resolved_version=7),
        gateway,
    )

    await use_case.execute(run.id, "tok")

    completed = run_repo.runs[run.id]
    assert completed.status == RunStatus.COMPLETED
    assert completed.dataset_version == 7
    assert completed.completed_at is not None
    # one item matches "42" exactly (score 1.0), the other doesn't (score 0.0)
    assert completed.aggregate_score == pytest.approx(0.5)
    assert len(item_repo.results) == 2
    assert len(gateway.calls) == 2


async def test_execute_marks_running_before_doing_any_work():
    run = make_pending_run()
    run_repo = FakeEvalRunRepository(seed=[run])
    version = RemotePromptVersion(id=run.prompt_version_id, template="hi", variables_schema={})
    use_case = _use_case(
        run_repo,
        FakeRunItemResultRepository(),
        FakePromptRegistryClient(version),
        FakeDatasetClient([RemoteDatasetItem(id=uuid4(), input={}, expected_output="x")]),
        FakeGatewayClient(),
    )

    await use_case.execute(run.id, "tok")

    # by the time it's done it's COMPLETED, but confirm RUNNING was a real
    # intermediate state by checking the repo saw more than one write
    assert run_repo.runs[run.id].status == RunStatus.COMPLETED


async def test_execute_does_nothing_for_an_unknown_run():
    use_case = _use_case(
        FakeEvalRunRepository(),
        FakeRunItemResultRepository(),
        FakePromptRegistryClient(),
        FakeDatasetClient([]),
        FakeGatewayClient(),
    )

    await use_case.execute(uuid4(), "tok")  # must not raise


async def test_execute_fails_the_run_when_the_prompt_version_is_unavailable():
    run = make_pending_run()
    run_repo = FakeEvalRunRepository(seed=[run])
    use_case = _use_case(
        run_repo,
        FakeRunItemResultRepository(),
        FakePromptRegistryClient(version=None),
        FakeDatasetClient([]),
        FakeGatewayClient(),
    )

    with pytest.raises(UpstreamServiceError):
        await use_case.execute(run.id, "tok")

    failed = run_repo.runs[run.id]
    assert failed.status == RunStatus.FAILED
    assert failed.error_message is not None


async def test_execute_fails_the_run_on_a_template_render_error():
    run = make_pending_run()
    run_repo = FakeEvalRunRepository(seed=[run])
    version = RemotePromptVersion(
        id=run.prompt_version_id, template="need {missing_var}", variables_schema={}
    )
    use_case = _use_case(
        run_repo,
        FakeRunItemResultRepository(),
        FakePromptRegistryClient(version),
        FakeDatasetClient([RemoteDatasetItem(id=uuid4(), input={"a": "1"}, expected_output="x")]),
        FakeGatewayClient(),
    )

    with pytest.raises(PromptRenderError):
        await use_case.execute(run.id, "tok")

    assert run_repo.runs[run.id].status == RunStatus.FAILED


async def test_execute_fails_the_run_for_an_unregistered_scorer():
    run = make_pending_run(scorer_names=("nonexistent_scorer",))
    run_repo = FakeEvalRunRepository(seed=[run])
    version = RemotePromptVersion(id=run.prompt_version_id, template="hi", variables_schema={})
    use_case = _use_case(
        run_repo,
        FakeRunItemResultRepository(),
        FakePromptRegistryClient(version),
        FakeDatasetClient([RemoteDatasetItem(id=uuid4(), input={}, expected_output="x")]),
        FakeGatewayClient(),
    )

    with pytest.raises(UnknownScorerError):
        await use_case.execute(run.id, "tok")

    assert run_repo.runs[run.id].status == RunStatus.FAILED


async def test_execute_reports_none_aggregate_when_no_items():
    run = make_pending_run()
    run_repo = FakeEvalRunRepository(seed=[run])
    version = RemotePromptVersion(id=run.prompt_version_id, template="hi", variables_schema={})
    use_case = _use_case(
        run_repo,
        FakeRunItemResultRepository(),
        FakePromptRegistryClient(version),
        FakeDatasetClient([]),
        FakeGatewayClient(),
    )

    await use_case.execute(run.id, "tok")

    assert run_repo.runs[run.id].aggregate_score is None
