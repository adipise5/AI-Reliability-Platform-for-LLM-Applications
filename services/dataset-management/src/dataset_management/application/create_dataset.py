from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from dataset_management.domain.entities import Dataset
from dataset_management.domain.errors import DuplicateDatasetNameError
from dataset_management.domain.ports import DatasetRepository


class CreateDatasetUseCase:
    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._dataset_repo = dataset_repo

    async def execute(self, *, org_id: UUID, name: str) -> Dataset:
        if await self._dataset_repo.get_by_org_and_name(org_id, name) is not None:
            raise DuplicateDatasetNameError(name)

        dataset = Dataset(
            id=uuid4(), org_id=org_id, name=name, current_version=0, created_at=datetime.now(UTC)
        )
        await self._dataset_repo.create(dataset)
        return dataset
