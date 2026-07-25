from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from experiment_tracking.application.add_run import AddRunUseCase
from experiment_tracking.domain.entities import Experiment
from experiment_tracking.domain.errors import ExperimentNotFoundError, RunNotFoundError
from tests.unit.conftest import FakeEvalRunReader, FakeExperimentRepository, make_run_summary


def _make_experiment(org_id) -> Experiment:
    return Experiment(id=uuid4(), org_id=org_id, name="e", description="", created_at=datetime.now(UTC))


async def test_execute_attaches_a_valid_run(org_id):
    experiment = _make_experiment(org_id)
    run = make_run_summary()
    repo = FakeExperimentRepository(seed=[experiment])
    reader = FakeEvalRunReader({run.id: run})
    use_case = AddRunUseCase(repo, reader)

    updated = await use_case.execute(
        org_id=org_id, experiment_id=experiment.id, run_id=run.id, credential="tok"
    )

    assert updated.run_ids == (run.id,)
    assert reader.get_run_calls == [run.id]


async def test_execute_is_idempotent_for_the_same_run(org_id):
    experiment = _make_experiment(org_id)
    run = make_run_summary()
    repo = FakeExperimentRepository(seed=[experiment])
    reader = FakeEvalRunReader({run.id: run})
    use_case = AddRunUseCase(repo, reader)

    await use_case.execute(org_id=org_id, experiment_id=experiment.id, run_id=run.id, credential="tok")
    updated = await use_case.execute(
        org_id=org_id, experiment_id=experiment.id, run_id=run.id, credential="tok"
    )

    assert updated.run_ids == (run.id,)


async def test_execute_rejects_a_run_the_evaluation_engine_does_not_recognize(org_id):
    experiment = _make_experiment(org_id)
    repo = FakeExperimentRepository(seed=[experiment])
    use_case = AddRunUseCase(repo, FakeEvalRunReader({}))

    with pytest.raises(RunNotFoundError):
        await use_case.execute(org_id=org_id, experiment_id=experiment.id, run_id=uuid4(), credential="tok")


async def test_execute_rejects_unknown_experiment(org_id):
    use_case = AddRunUseCase(FakeExperimentRepository(), FakeEvalRunReader())

    with pytest.raises(ExperimentNotFoundError):
        await use_case.execute(org_id=org_id, experiment_id=uuid4(), run_id=uuid4(), credential="tok")
