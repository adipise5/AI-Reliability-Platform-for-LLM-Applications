"""Domain entities for Dataset Management — see ADR-0001: no framework
imports here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Dataset:
    """`current_version` starts at 0 ("no items imported yet") and
    advances by one on every bulk import. Items are immutable once
    imported — importing again creates a new version snapshot rather than
    mutating the last one, so an eval run that pinned a version keeps
    seeing exactly what it saw originally."""

    id: UUID
    org_id: UUID
    name: str
    current_version: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class DatasetItem:
    id: UUID
    dataset_id: UUID
    version: int
    input: dict[str, Any]
    expected_output: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, slots=True)
class NewDatasetItem:
    """An item as submitted for import — no id/version yet; the use case
    assigns those once it knows what version this batch becomes."""

    input: dict[str, Any]
    expected_output: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ImportResult:
    dataset_id: UUID
    version: int
    item_count: int
