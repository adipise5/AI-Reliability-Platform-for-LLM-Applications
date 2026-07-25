from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from experiment_tracking.application.compare_experiment import CompareExperimentUseCase
from experiment_tracking.domain.entities import Experiment
from experiment_tracking.domain.errors import ExperimentNotFoundError
from tests.unit.conftest import FakeEvalRunReader, FakeExperimentRepository, make_run_summary


async def test_execute_fetches_every_linked_run(org_id):
    run_a, run_b = make_run_summary(), make_run_summary()
    experiment = Experiment(
        id=uuid4(),
        org_id=org_id,
        name="e",
        description="",
        created_at=datetime.now(UTC),
        run_ids=(run_a.id, run_b.id),
    )
    repo = FakeExperimentRepository(seed=[experiment])
    reader = FakeEvalRunReader({run_a.id: run_a, run_b.id: run_b})
    use_case = CompareExperimentUseCase(repo, reader)

    fetched_experiment, runs = await use_case.execute(
        org_id=org_id, experiment_id=experiment.id, credential="tok"
    )

    assert fetched_experiment == experiment
    assert {r.id for r in runs} == {run_a.id, run_b.id}


async def test_execute_returns_empty_list_for_an_experiment_with_no_runs(org_id):
    experiment = Experiment(id=uuid4(), org_id=org_id, name="e", description="", created_at=datetime.now(UTC))
    repo = FakeExperimentRepository(seed=[experiment])
    use_case = CompareExperimentUseCase(repo, FakeEvalRunReader())

    _, runs = await use_case.execute(org_id=org_id, experiment_id=experiment.id, credential="tok")

    assert runs == []


async def test_execute_rejects_unknown_experiment(org_id):
    use_case = CompareExperimentUseCase(FakeExperimentRepository(), FakeEvalRunReader())

    with pytest.raises(ExperimentNotFoundError):
        await use_case.execute(org_id=org_id, experiment_id=uuid4(), credential="tok")
