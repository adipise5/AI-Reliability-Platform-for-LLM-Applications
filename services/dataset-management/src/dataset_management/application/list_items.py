"""Also doubles as "export" — a GET of every item in a version is a JSON
export; there's no separate export use case duplicating this one."""

from __future__ import annotations

from uuid import UUID

from dataset_management.domain.entities import DatasetItem
from dataset_management.domain.errors import DatasetNotFoundError
from dataset_management.domain.ports import DatasetItemRepository, DatasetRepository


class ListItemsUseCase:
    def __init__(self, dataset_repo: DatasetRepository, item_repo: DatasetItemRepository) -> None:
        self._dataset_repo = dataset_repo
        self._item_repo = item_repo

    async def execute(
        self, *, org_id: UUID, dataset_id: UUID, version: int | None = None
    ) -> list[DatasetItem]:
        dataset = await self._dataset_repo.get_by_id(dataset_id)
        if dataset is None or dataset.org_id != org_id:
            raise DatasetNotFoundError(dataset_id)

        target_version = version if version is not None else dataset.current_version
        return await self._item_repo.list_by_version(dataset_id, target_version)
