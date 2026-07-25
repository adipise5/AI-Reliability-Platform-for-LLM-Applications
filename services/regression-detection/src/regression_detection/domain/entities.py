"""Domain entities for the Regression Detection Engine — see ADR-0001: no
framework imports here.

Two independent features live in this service, per the original service
catalog's "Baselines, drift, gate decisions" and its dependency on both
Experiment Tracking (by way of the Evaluation Engine, per ADR-0005) and
the Trace Collector:

- **Eval-run gating** (`Baseline`, `GateDecision`) — is a completed run's
  score a statistically significant drop from this prompt's history? This
  is what the GitHub Integration (Week 13) calls for a CI gate.
- **Latency anomaly checks** (`LatencyAnomalyCheck`) — is the Gateway
  getting slower right now, compared to its own recent history? A
  stateless computation over the Trace Collector's trace summaries, not
  persisted — see application/check_latency_anomaly.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class GateVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True, slots=True)
class Baseline:
    """A statistically-derived acceptable range, not a fixed threshold —
    recomputed from the prompt's own run history each time a run is
    gated, rather than incrementally updated, so it's always an honest
    reflection of "every completed run so far," auditable by re-deriving
    it from source."""

    id: UUID
    org_id: UUID
    prompt_id: UUID
    mean_score: float
    stddev_score: float
    sample_size: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class GateDecision:
    id: UUID
    org_id: UUID
    prompt_id: UUID
    run_id: UUID
    observed_score: float
    baseline_mean: float
    baseline_stddev: float
    verdict: GateVerdict
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RemoteEvalRun:
    id: UUID
    prompt_id: UUID
    status: str
    aggregate_score: float | None


@dataclass(frozen=True, slots=True)
class RemoteTraceSummary:
    trace_id: str
    status: str
    duration_ms: float


@dataclass(frozen=True, slots=True)
class LatencyAnomalyCheck:
    sample_count: int
    recent_mean_ms: float | None
    baseline_mean_ms: float | None
    baseline_stddev_ms: float | None
    is_anomalous: bool
    insufficient_data: bool
