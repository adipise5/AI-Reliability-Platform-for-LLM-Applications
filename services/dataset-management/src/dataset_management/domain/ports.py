from __future__ import annotations

from typing import Protocol
from uuid import UUID

from dataset_management.domain.entities import Dataset, DatasetItem


class DatasetRepository(Protocol):
    async def create(self, dataset: Dataset) -> None: ...

    async def get_by_id(self, dataset_id: UUID) -> Dataset | None: ...

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Dataset | None: ...

    async def set_current_version(self, dataset_id: UUID, version: int) -> None: ...


class DatasetItemRepository(Protocol):
    async def bulk_create(self, items: list[DatasetItem]) -> None: ...

    async def list_by_version(self, dataset_id: UUID, version: int) -> list[DatasetItem]: ...
