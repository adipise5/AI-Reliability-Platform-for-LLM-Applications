"""Domain entities for the Report Generator — see ADR-0001: no framework
imports here.

`RemoteExperiment` and `RemoteRunSummary` are value objects for data owned
by Experiment Tracking (which itself just aggregates the Evaluation
Engine — see ADR-0005). This service never writes back to that data; it
only reads a snapshot at generation time and renders it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ReportFormat(StrEnum):
    HTML = "html"
    PDF = "pdf"


class ReportStatus(StrEnum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Report:
    id: UUID
    org_id: UUID
    experiment_id: UUID
    format: ReportFormat
    status: ReportStatus
    created_at: datetime
    content: bytes | None = None
    error_message: str | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RemoteRunSummary:
    id: UUID
    prompt_id: UUID
    model: str
    status: str
    aggregate_score: float | None
    created_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class RemoteExperiment:
    id: UUID
    name: str
    description: str
    run_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RemoteExperimentComparison:
    experiment: RemoteExperiment
    runs: tuple[RemoteRunSummary, ...] = field(default_factory=tuple)
