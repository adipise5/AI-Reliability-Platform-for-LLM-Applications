from __future__ import annotations

from uuid import uuid4

import pytest

from dataset_management.application.get_dataset import GetDatasetUseCase
from dataset_management.domain.errors import DatasetNotFoundError
from tests.unit.conftest import FakeDatasetRepository


async def test_execute_returns_an_owned_dataset(org_id, sample_dataset):
    repo = FakeDatasetRepository(seed=[sample_dataset])
    use_case = GetDatasetUseCase(repo)

    result = await use_case.execute(org_id=org_id, dataset_id=sample_dataset.id)

    assert result == sample_dataset


async def test_execute_rejects_a_dataset_owned_by_another_org(sample_dataset):
    repo = FakeDatasetRepository(seed=[sample_dataset])
    use_case = GetDatasetUseCase(repo)

    with pytest.raises(DatasetNotFoundError):
        await use_case.execute(org_id=uuid4(), dataset_id=sample_dataset.id)


async def test_execute_rejects_unknown_dataset(org_id):
    use_case = GetDatasetUseCase(FakeDatasetRepository())

    with pytest.raises(DatasetNotFoundError):
        await use_case.execute(org_id=org_id, dataset_id=uuid4())
