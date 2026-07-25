"""Domain entities for Experiment Tracking — see ADR-0001: no framework
imports here.

Per ADR-0005, this service is an **aggregation and comparison layer**,
not a second store of run results: `Experiment` is a lightweight,
locally-owned grouping of run ids; `RemoteEvalRunSummary` is a value
object for data owned by the Evaluation Engine, fetched fresh on every
read rather than copied in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Experiment:
    id: UUID
    org_id: UUID
    name: str
    description: str
    created_at: datetime
    run_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RemoteEvalRunSummary:
    id: UUID
    prompt_id: UUID
    prompt_version_id: UUID
    dataset_id: UUID
    dataset_version: int | None
    model: str
    status: str
    aggregate_score: float | None
    created_at: datetime
    completed_at: datetime | None
