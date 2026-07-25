from __future__ import annotations

from uuid import UUID

from dataset_management.domain.entities import Dataset
from dataset_management.domain.errors import DatasetNotFoundError
from dataset_management.domain.ports import DatasetRepository


class GetDatasetUseCase:
    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._dataset_repo = dataset_repo

    async def execute(self, *, org_id: UUID, dataset_id: UUID) -> Dataset:
        dataset = await self._dataset_repo.get_by_id(dataset_id)
        if dataset is None or dataset.org_id != org_id:
            raise DatasetNotFoundError(dataset_id)
        return dataset
