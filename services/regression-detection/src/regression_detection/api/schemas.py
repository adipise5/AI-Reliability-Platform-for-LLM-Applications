from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from regression_detection.domain.entities import Baseline, GateDecision, LatencyAnomalyCheck


class GateRunIn(BaseModel):
    run_id: UUID


class BaselineOut(BaseModel):
    id: UUID
    org_id: UUID
    prompt_id: UUID
    mean_score: float
    stddev_score: float
    sample_size: int
    updated_at: datetime

    @classmethod
    def from_domain(cls, baseline: Baseline) -> BaselineOut:
        return cls(
            id=baseline.id,
            org_id=baseline.org_id,
            prompt_id=baseline.prompt_id,
            mean_score=baseline.mean_score,
            stddev_score=baseline.stddev_score,
            sample_size=baseline.sample_size,
            updated_at=baseline.updated_at,
        )


class GateDecisionOut(BaseModel):
    id: UUID
    org_id: UUID
    prompt_id: UUID
    run_id: UUID
    observed_score: float
    baseline_mean: float
    baseline_stddev: float
    verdict: str
    created_at: datetime

    @classmethod
    def from_domain(cls, decision: GateDecision) -> GateDecisionOut:
        return cls(
            id=decision.id,
            org_id=decision.org_id,
            prompt_id=decision.prompt_id,
            run_id=decision.run_id,
            observed_score=decision.observed_score,
            baseline_mean=decision.baseline_mean,
            baseline_stddev=decision.baseline_stddev,
            verdict=decision.verdict.value,
            created_at=decision.created_at,
        )


class LatencyAnomalyOut(BaseModel):
    sample_count: int
    recent_mean_ms: float | None
    baseline_mean_ms: float | None
    baseline_stddev_ms: float | None
    is_anomalous: bool
    insufficient_data: bool

    @classmethod
    def from_domain(cls, check: LatencyAnomalyCheck) -> LatencyAnomalyOut:
        return cls(
            sample_count=check.sample_count,
            recent_mean_ms=check.recent_mean_ms,
            baseline_mean_ms=check.baseline_mean_ms,
            baseline_stddev_ms=check.baseline_stddev_ms,
            is_anomalous=check.is_anomalous,
            insufficient_data=check.insufficient_data,
        )


class ErrorOut(BaseModel):
    type: str
    message: str
