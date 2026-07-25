"""Domain entities for the Dashboard Backend — see ADR-0001: no framework
imports here.

Every entity here is a value object for data owned by *another* bounded
context — this service is the one exception in the catalog that owns no
data of its own at all (no schema, no Alembic migrations — see
`infrastructure/`). Its only job is to fetch from the read-facing
services the React Dashboard (Week 15) needs and assemble the shapes a
UI actually renders, either 1:1 or, for `DashboardOverview`, merged from
several services at once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RemoteEvalRun:
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


@dataclass(frozen=True, slots=True)
class RemoteScore:
    scorer_name: str
    value: float


@dataclass(frozen=True, slots=True)
class RemoteRunItemResult:
    id: UUID
    dataset_item_id: UUID
    output: str
    latency_ms: float
    scores: tuple[RemoteScore, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RemoteGateDecision:
    run_id: UUID
    verdict: str
    observed_score: float
    baseline_mean: float
    baseline_stddev: float


@dataclass(frozen=True, slots=True)
class RunDetail:
    run: RemoteEvalRun
    items: tuple[RemoteRunItemResult, ...]
    gate_decision: RemoteGateDecision | None


@dataclass(frozen=True, slots=True)
class RemoteModelUsage:
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


@dataclass(frozen=True, slots=True)
class RemoteUsageSummary:
    total_cost_usd: float
    total_prompt_tokens: int
    total_completion_tokens: int
    by_model: tuple[RemoteModelUsage, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RemoteBudgetStatus:
    spent_this_month_usd: float
    limit_usd: float | None
    remaining_usd: float | None
    over_budget: bool


@dataclass(frozen=True, slots=True)
class RemoteBaseline:
    prompt_id: UUID
    mean_score: float
    stddev_score: float
    sample_size: int


@dataclass(frozen=True, slots=True)
class RemoteLatencyAnomaly:
    sample_count: int
    recent_mean_ms: float | None
    baseline_mean_ms: float | None
    baseline_stddev_ms: float | None
    is_anomalous: bool
    insufficient_data: bool


@dataclass(frozen=True, slots=True)
class RemoteReport:
    id: UUID
    experiment_id: UUID
    format: str
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class RemoteChannel:
    id: UUID
    channel_type: str
    name: str
    target: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class RemoteNotification:
    id: UUID
    channel_id: UUID
    subject: str
    status: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RemoteCheckRun:
    id: UUID
    repo: str
    commit_sha: str
    status: str
    conclusion: str | None
    run_id: UUID | None


@dataclass(frozen=True, slots=True)
class RemoteTraceSummary:
    trace_id: str
    root_span_name: str
    span_count: int
    status: str
    duration_ms: float


@dataclass(frozen=True, slots=True)
class DashboardOverview:
    """Deliberately tolerant of partial upstream failure — see
    `GetDashboardOverviewUseCase`. A `None` field means that particular
    service didn't answer in time, not that the org has no data."""

    recent_runs: tuple[RemoteEvalRun, ...]
    cost_summary: RemoteUsageSummary | None
    budget_status: RemoteBudgetStatus | None
    latency_anomaly: RemoteLatencyAnomaly | None
    recent_notifications: tuple[RemoteNotification, ...]
