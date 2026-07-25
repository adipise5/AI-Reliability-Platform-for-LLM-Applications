from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from evaluation_engine.domain.entities import EvalRun, RunItemResult, Score


class TriggerRunIn(BaseModel):
    prompt_id: UUID
    prompt_version_id: UUID
    dataset_id: UUID
    model: str = Field(..., min_length=1)
    dataset_version: int | None = Field(default=None, ge=1)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    scorer_names: list[str] | None = None


class ScoreOut(BaseModel):
    scorer_name: str
    value: float
    evidence: dict[str, Any]

    @classmethod
    def from_domain(cls, score: Score) -> ScoreOut:
        return cls(scorer_name=score.scorer_name, value=score.value, evidence=score.evidence)


class EvalRunOut(BaseModel):
    id: UUID
    org_id: UUID
    prompt_id: UUID
    prompt_version_id: UUID
    dataset_id: UUID
    dataset_version: int | None
    model: str
    scorer_names: list[str]
    status: str
    temperature: float
    max_tokens: int | None
    aggregate_score: float | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, run: EvalRun) -> EvalRunOut:
        return cls(
            id=run.id,
            org_id=run.org_id,
            prompt_id=run.prompt_id,
            prompt_version_id=run.prompt_version_id,
            dataset_id=run.dataset_id,
            dataset_version=run.dataset_version,
            model=run.model,
            scorer_names=list(run.scorer_names),
            status=run.status.value,
            temperature=run.temperature,
            max_tokens=run.max_tokens,
            aggregate_score=run.aggregate_score,
            error_message=run.error_message,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )


class RunItemResultOut(BaseModel):
    id: UUID
    dataset_item_id: UUID
    output: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    scores: list[ScoreOut]
    created_at: datetime

    @classmethod
    def from_domain(cls, item: RunItemResult) -> RunItemResultOut:
        return cls(
            id=item.id,
            dataset_item_id=item.dataset_item_id,
            output=item.output,
            latency_ms=item.latency_ms,
            prompt_tokens=item.prompt_tokens,
            completion_tokens=item.completion_tokens,
            scores=[ScoreOut.from_domain(s) for s in item.scores],
            created_at=item.created_at,
        )


class EvalRunDetailOut(BaseModel):
    run: EvalRunOut
    items: list[RunItemResultOut]


class ErrorOut(BaseModel):
    type: str
    message: str
