from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from experiment_tracking.application.get_experiment import GetExperimentUseCase
from experiment_tracking.domain.entities import Experiment
from experiment_tracking.domain.errors import ExperimentNotFoundError
from tests.unit.conftest import FakeExperimentRepository


def _make_experiment(org_id) -> Experiment:
    return Experiment(id=uuid4(), org_id=org_id, name="e", description="", created_at=datetime.now(UTC))


async def test_execute_returns_an_owned_experiment(org_id):
    experiment = _make_experiment(org_id)
    use_case = GetExperimentUseCase(FakeExperimentRepository(seed=[experiment]))

    result = await use_case.execute(org_id=org_id, experiment_id=experiment.id)

    assert result == experiment


async def test_execute_rejects_an_experiment_from_another_org(org_id):
    experiment = _make_experiment(org_id)
    use_case = GetExperimentUseCase(FakeExperimentRepository(seed=[experiment]))

    with pytest.raises(ExperimentNotFoundError):
        await use_case.execute(org_id=uuid4(), experiment_id=experiment.id)


async def test_execute_rejects_unknown_experiment(org_id):
    use_case = GetExperimentUseCase(FakeExperimentRepository())

    with pytest.raises(ExperimentNotFoundError):
        await use_case.execute(org_id=org_id, experiment_id=uuid4())
