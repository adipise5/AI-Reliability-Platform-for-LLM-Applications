from __future__ import annotations

from uuid import UUID


class DatasetManagementError(Exception):
    """Base class for all domain errors raised by Dataset Management."""


class DatasetNotFoundError(DatasetManagementError):
    def __init__(self, dataset_id: UUID) -> None:
        self.dataset_id = dataset_id
        super().__init__(f"no dataset {dataset_id} in this org")


class DuplicateDatasetNameError(DatasetManagementError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"a dataset named {name!r} already exists in this org")


class EmptyImportError(DatasetManagementError):
    def __init__(self) -> None:
        super().__init__("bulk import requires at least one item")
