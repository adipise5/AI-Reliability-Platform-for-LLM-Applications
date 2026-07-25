from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from dataset_management.domain.entities import Dataset, DatasetItem, ImportResult, NewDatasetItem


class CreateDatasetIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class DatasetOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    current_version: int
    created_at: datetime

    @classmethod
    def from_domain(cls, dataset: Dataset) -> DatasetOut:
        return cls(
            id=dataset.id,
            org_id=dataset.org_id,
            name=dataset.name,
            current_version=dataset.current_version,
            created_at=dataset.created_at,
        )


class NewItemIn(BaseModel):
    input: dict[str, Any]
    expected_output: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_domain(self) -> NewDatasetItem:
        return NewDatasetItem(
            input=self.input, expected_output=self.expected_output, metadata=self.metadata
        )


class BulkImportIn(BaseModel):
    items: list[NewItemIn] = Field(..., min_length=1)


class ImportResultOut(BaseModel):
    dataset_id: UUID
    version: int
    item_count: int

    @classmethod
    def from_domain(cls, result: ImportResult) -> ImportResultOut:
        return cls(dataset_id=result.dataset_id, version=result.version, item_count=result.item_count)


class DatasetItemOut(BaseModel):
    id: UUID
    dataset_id: UUID
    version: int
    input: dict[str, Any]
    expected_output: Any
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def from_domain(cls, item: DatasetItem) -> DatasetItemOut:
        return cls(
            id=item.id,
            dataset_id=item.dataset_id,
            version=item.version,
            input=item.input,
            expected_output=item.expected_output,
            metadata=item.metadata,
            created_at=item.created_at,
        )


class ErrorOut(BaseModel):
    type: str
    message: str
