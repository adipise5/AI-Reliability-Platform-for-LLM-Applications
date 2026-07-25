from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from dataset_management.domain.entities import Dataset, DatasetItem


class FakeDatasetRepository:
    def __init__(self, seed: list[Dataset] | None = None) -> None:
        self.datasets: dict[UUID, Dataset] = {d.id: d for d in (seed or [])}

    async def create(self, dataset: Dataset) -> None:
        self.datasets[dataset.id] = dataset

    async def get_by_id(self, dataset_id: UUID) -> Dataset | None:
        return self.datasets.get(dataset_id)

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Dataset | None:
        return next(
            (d for d in self.datasets.values() if d.org_id == org_id and d.name == name), None
        )

    async def set_current_version(self, dataset_id: UUID, version: int) -> None:
        current = self.datasets[dataset_id]
        self.datasets[dataset_id] = Dataset(
            id=current.id,
            org_id=current.org_id,
            name=current.name,
            current_version=version,
            created_at=current.created_at,
        )


class FakeDatasetItemRepository:
    def __init__(self, seed: list[DatasetItem] | None = None) -> None:
        self.items: list[DatasetItem] = list(seed or [])

    async def bulk_create(self, items: list[DatasetItem]) -> None:
        self.items.extend(items)

    async def list_by_version(self, dataset_id: UUID, version: int) -> list[DatasetItem]:
        return [i for i in self.items if i.dataset_id == dataset_id and i.version == version]


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_dataset(org_id: UUID) -> Dataset:
    return Dataset(
        id=uuid4(), org_id=org_id, name="qa-golden-set", current_version=0, created_at=datetime.now(UTC)
    )
