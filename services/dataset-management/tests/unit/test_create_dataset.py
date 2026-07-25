from __future__ import annotations

import pytest

from dataset_management.application.create_dataset import CreateDatasetUseCase
from dataset_management.domain.errors import DuplicateDatasetNameError
from tests.unit.conftest import FakeDatasetRepository


async def test_execute_creates_a_dataset_at_version_zero(org_id):
    repo = FakeDatasetRepository()
    use_case = CreateDatasetUseCase(repo)

    dataset = await use_case.execute(org_id=org_id, name="qa-golden-set")

    assert repo.datasets[dataset.id] is dataset
    assert dataset.current_version == 0


async def test_execute_rejects_duplicate_name_within_the_same_org(org_id, sample_dataset):
    repo = FakeDatasetRepository(seed=[sample_dataset])
    use_case = CreateDatasetUseCase(repo)

    with pytest.raises(DuplicateDatasetNameError):
        await use_case.execute(org_id=org_id, name=sample_dataset.name)
