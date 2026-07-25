from __future__ import annotations

from uuid import uuid4

import pytest

from regression_detection.application.evaluate_run import EvaluateRunUseCase
from regression_detection.domain.entities import GateVerdict
from regression_detection.domain.errors import RunNotCompletedError
from tests.unit.conftest import (
    FakeBaselineRepository,
    FakeEvalRunReader,
    FakeGateDecisionRepository,
    make_run,
)

_UseCaseAndRepos = tuple[EvaluateRunUseCase, FakeBaselineRepository, FakeGateDecisionRepository]


def _use_case(reader: FakeEvalRunReader) -> _UseCaseAndRepos:
    baselines = FakeBaselineRepository()
    decisions = FakeGateDecisionRepository()
    return EvaluateRunUseCase(reader, baselines, decisions), baselines, decisions


async def test_run_not_completed_raises(org_id):
    run = make_run(status="running", aggregate_score=None)
    reader = FakeEvalRunReader({run.id: run})
    use_case, _, _ = _use_case(reader)

    with pytest.raises(RunNotCompletedError):
        await use_case.execute(org_id=org_id, credential="tok", run_id=run.id)


async def test_first_completed_run_for_a_prompt_passes_and_seeds_baseline(org_id):
    prompt_id = uuid4()
    run = make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.9)
    reader = FakeEvalRunReader({run.id: run})
    use_case, baselines, decisions = _use_case(reader)

    decision = await use_case.execute(org_id=org_id, credential="tok", run_id=run.id)

    assert decision.verdict == GateVerdict.PASS
    assert decision.baseline_mean == 0.9
    assert decision.baseline_stddev == 0.0
    seeded = await baselines.get_by_prompt(org_id, prompt_id)
    assert seeded is not None
    assert seeded.sample_size == 1
    assert len(decisions.decisions) == 1


async def test_passes_when_within_review_threshold(org_id):
    prompt_id = uuid4()
    run = make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.85)
    priors = [
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=1.0),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=1.0),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.8),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.8),
    ]
    reader = FakeEvalRunReader({r.id: r for r in [run, *priors]})
    use_case, _, _ = _use_case(reader)

    decision = await use_case.execute(org_id=org_id, credential="tok", run_id=run.id)

    assert decision.verdict == GateVerdict.PASS


async def test_needs_review_between_thresholds(org_id):
    prompt_id = uuid4()
    run = make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.75)
    priors = [
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=1.0),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=1.0),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.8),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.8),
    ]
    reader = FakeEvalRunReader({r.id: r for r in [run, *priors]})
    use_case, _, _ = _use_case(reader)

    decision = await use_case.execute(org_id=org_id, credential="tok", run_id=run.id)

    assert decision.verdict == GateVerdict.NEEDS_REVIEW


async def test_fails_beyond_fail_threshold(org_id):
    prompt_id = uuid4()
    run = make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.65)
    priors = [
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=1.0),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=1.0),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.8),
        make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.8),
    ]
    reader = FakeEvalRunReader({r.id: r for r in [run, *priors]})
    use_case, _, _ = _use_case(reader)

    decision = await use_case.execute(org_id=org_id, credential="tok", run_id=run.id)

    assert decision.verdict == GateVerdict.FAIL


async def test_zero_stddev_baseline_fails_below_mean(org_id):
    prompt_id = uuid4()
    run = make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.85)
    priors = [make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.9) for _ in range(3)]
    reader = FakeEvalRunReader({r.id: r for r in [run, *priors]})
    use_case, _, _ = _use_case(reader)

    decision = await use_case.execute(org_id=org_id, credential="tok", run_id=run.id)

    assert decision.verdict == GateVerdict.FAIL
    assert decision.baseline_stddev == 0.0


async def test_zero_stddev_baseline_passes_at_or_above_mean(org_id):
    prompt_id = uuid4()
    run = make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.95)
    priors = [make_run(prompt_id=prompt_id, status="completed", aggregate_score=0.9) for _ in range(3)]
    reader = FakeEvalRunReader({r.id: r for r in [run, *priors]})
    use_case, _, _ = _use_case(reader)

    decision = await use_case.execute(org_id=org_id, credential="tok", run_id=run.id)

    assert decision.verdict == GateVerdict.PASS
