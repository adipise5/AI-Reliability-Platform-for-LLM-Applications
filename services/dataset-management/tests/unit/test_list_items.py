from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from dataset_management.application.list_items import ListItemsUseCase
from dataset_management.domain.entities import DatasetItem
from dataset_management.domain.errors import DatasetNotFoundError
from tests.unit.conftest import FakeDatasetItemRepository, FakeDatasetRepository


def _make_item(dataset_id, version) -> DatasetItem:
    from datetime import UTC, datetime

    return DatasetItem(
        id=uuid4(), dataset_id=dataset_id, version=version, input={"q": "x"}, created_at=datetime.now(UTC)
    )


async def test_execute_defaults_to_the_current_version(org_id, sample_dataset):
    dataset_at_v2 = replace(sample_dataset, current_version=2)
    v1_item = _make_item(sample_dataset.id, 1)
    v2_item = _make_item(sample_dataset.id, 2)
    dataset_repo = FakeDatasetRepository(seed=[dataset_at_v2])
    item_repo = FakeDatasetItemRepository(seed=[v1_item, v2_item])
    use_case = ListItemsUseCase(dataset_repo, item_repo)

    items = await use_case.execute(org_id=org_id, dataset_id=sample_dataset.id)

    assert [i.id for i in items] == [v2_item.id]


async def test_execute_can_request_an_older_version_explicitly(org_id, sample_dataset):
    dataset_at_v2 = replace(sample_dataset, current_version=2)
    v1_item = _make_item(sample_dataset.id, 1)
    v2_item = _make_item(sample_dataset.id, 2)
    dataset_repo = FakeDatasetRepository(seed=[dataset_at_v2])
    item_repo = FakeDatasetItemRepository(seed=[v1_item, v2_item])
    use_case = ListItemsUseCase(dataset_repo, item_repo)

    items = await use_case.execute(org_id=org_id, dataset_id=sample_dataset.id, version=1)

    assert [i.id for i in items] == [v1_item.id]


async def test_execute_rejects_unknown_dataset(org_id):
    use_case = ListItemsUseCase(FakeDatasetRepository(), FakeDatasetItemRepository())

    with pytest.raises(DatasetNotFoundError):
        await use_case.execute(org_id=org_id, dataset_id=uuid4())
