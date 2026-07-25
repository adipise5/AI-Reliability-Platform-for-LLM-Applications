from __future__ import annotations

from uuid import uuid4

import pytest

from dataset_management.application.import_items import ImportItemsUseCase
from dataset_management.domain.entities import NewDatasetItem
from dataset_management.domain.errors import DatasetNotFoundError, EmptyImportError
from tests.unit.conftest import FakeDatasetItemRepository, FakeDatasetRepository


async def test_execute_imports_a_new_version_and_advances_the_dataset(org_id, sample_dataset):
    dataset_repo = FakeDatasetRepository(seed=[sample_dataset])
    item_repo = FakeDatasetItemRepository()
    use_case = ImportItemsUseCase(dataset_repo, item_repo)
    items = [NewDatasetItem(input={"q": "2+2"}, expected_output="4")]

    result = await use_case.execute(org_id=org_id, dataset_id=sample_dataset.id, items=items)

    assert result.version == 1
    assert result.item_count == 1
    assert dataset_repo.datasets[sample_dataset.id].current_version == 1
    assert len(item_repo.items) == 1
    assert item_repo.items[0].version == 1


async def test_execute_advances_version_on_each_successive_import(org_id, sample_dataset):
    dataset_repo = FakeDatasetRepository(seed=[sample_dataset])
    item_repo = FakeDatasetItemRepository()
    use_case = ImportItemsUseCase(dataset_repo, item_repo)

    first = await use_case.execute(
        org_id=org_id, dataset_id=sample_dataset.id, items=[NewDatasetItem(input={"q": "a"})]
    )
    second = await use_case.execute(
        org_id=org_id, dataset_id=sample_dataset.id, items=[NewDatasetItem(input={"q": "b"})]
    )

    assert first.version == 1
    assert second.version == 2
    # Both versions remain queryable, independently.
    assert len([i for i in item_repo.items if i.version == 1]) == 1
    assert len([i for i in item_repo.items if i.version == 2]) == 1


async def test_execute_rejects_an_empty_batch(org_id, sample_dataset):
    dataset_repo = FakeDatasetRepository(seed=[sample_dataset])
    use_case = ImportItemsUseCase(dataset_repo, FakeDatasetItemRepository())

    with pytest.raises(EmptyImportError):
        await use_case.execute(org_id=org_id, dataset_id=sample_dataset.id, items=[])


async def test_execute_rejects_unknown_dataset(org_id):
    use_case = ImportItemsUseCase(FakeDatasetRepository(), FakeDatasetItemRepository())

    with pytest.raises(DatasetNotFoundError):
        await use_case.execute(
            org_id=org_id, dataset_id=uuid4(), items=[NewDatasetItem(input={"q": "a"})]
        )
