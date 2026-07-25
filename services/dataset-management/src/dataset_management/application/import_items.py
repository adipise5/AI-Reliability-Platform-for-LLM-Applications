from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from dataset_management.domain.entities import DatasetItem, ImportResult, NewDatasetItem
from dataset_management.domain.errors import DatasetNotFoundError, EmptyImportError
from dataset_management.domain.ports import DatasetItemRepository, DatasetRepository


class ImportItemsUseCase:
    def __init__(self, dataset_repo: DatasetRepository, item_repo: DatasetItemRepository) -> None:
        self._dataset_repo = dataset_repo
        self._item_repo = item_repo

    async def execute(
        self, *, org_id: UUID, dataset_id: UUID, items: list[NewDatasetItem]
    ) -> ImportResult:
        if not items:
            raise EmptyImportError

        dataset = await self._dataset_repo.get_by_id(dataset_id)
        if dataset is None or dataset.org_id != org_id:
            raise DatasetNotFoundError(dataset_id)

        new_version = dataset.current_version + 1
        now = datetime.now(UTC)
        persisted = [
            DatasetItem(
                id=uuid4(),
                dataset_id=dataset_id,
                version=new_version,
                input=item.input,
                expected_output=item.expected_output,
                metadata=item.metadata,
                created_at=now,
            )
            for item in items
        ]
        await self._item_repo.bulk_create(persisted)
        await self._dataset_repo.set_current_version(dataset_id, new_version)

        return ImportResult(dataset_id=dataset_id, version=new_version, item_count=len(persisted))
