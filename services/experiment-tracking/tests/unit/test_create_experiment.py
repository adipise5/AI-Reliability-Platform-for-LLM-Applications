from __future__ import annotations

import pytest

from experiment_tracking.application.create_experiment import CreateExperimentUseCase
from experiment_tracking.domain.errors import DuplicateExperimentNameError
from tests.unit.conftest import FakeExperimentRepository


async def test_execute_creates_an_experiment(org_id):
    repo = FakeExperimentRepository()
    use_case = CreateExperimentUseCase(repo)

    experiment = await use_case.execute(org_id=org_id, name="rollout-v2", description="testing v2")

    assert repo.experiments[experiment.id] is experiment
    assert experiment.run_ids == ()
    assert experiment.description == "testing v2"


async def test_execute_rejects_duplicate_name_within_org(org_id):
    repo = FakeExperimentRepository()
    use_case = CreateExperimentUseCase(repo)
    await use_case.execute(org_id=org_id, name="rollout-v2")

    with pytest.raises(DuplicateExperimentNameError):
        await use_case.execute(org_id=org_id, name="rollout-v2")
