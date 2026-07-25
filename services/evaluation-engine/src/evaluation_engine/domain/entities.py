"""Domain entities for the Evaluation Engine — see ADR-0001: no framework
imports here.

`RemotePromptVersion`, `RemoteDatasetItem`, and `RemoteCompletion` are
value objects for data owned by *other* bounded contexts (Prompt
Registry, Dataset Management, the Gateway) — see domain/ports.py. They're
domain types here because the use cases operate on them directly, but
this service never writes back to those other services' data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class EvalRun:
    id: UUID
    org_id: UUID
    prompt_id: UUID
    prompt_version_id: UUID
    dataset_id: UUID
    model: str
    scorer_names: tuple[str, ...]
    status: RunStatus
    created_at: datetime
    dataset_version: int | None = None
    temperature: float = 1.0
    max_tokens: int | None = None
    aggregate_score: float | None = None
    error_message: str | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Score:
    scorer_name: str
    value: float
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunItemResult:
    id: UUID
    run_id: UUID
    dataset_item_id: UUID
    output: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    scores: tuple[Score, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, slots=True)
class RemotePromptVersion:
    id: UUID
    template: str
    variables_schema: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RemoteDatasetItem:
    id: UUID
    input: dict[str, Any]
    expected_output: Any = None


@dataclass(frozen=True, slots=True)
class RemoteCompletion:
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
