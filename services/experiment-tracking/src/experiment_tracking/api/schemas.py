from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from experiment_tracking.domain.entities import Experiment, RemoteEvalRunSummary


class CreateExperimentIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""


class ExperimentOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    description: str
    run_ids: list[UUID]
    created_at: datetime

    @classmethod
    def from_domain(cls, experiment: Experiment) -> ExperimentOut:
        return cls(
            id=experiment.id,
            org_id=experiment.org_id,
            name=experiment.name,
            description=experiment.description,
            run_ids=list(experiment.run_ids),
            created_at=experiment.created_at,
        )


class AddRunIn(BaseModel):
    run_id: UUID


class RemoteEvalRunSummaryOut(BaseModel):
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

    @classmethod
    def from_domain(cls, run: RemoteEvalRunSummary) -> RemoteEvalRunSummaryOut:
        return cls(
            id=run.id,
            prompt_id=run.prompt_id,
            prompt_version_id=run.prompt_version_id,
            dataset_id=run.dataset_id,
            dataset_version=run.dataset_version,
            model=run.model,
            status=run.status,
            aggregate_score=run.aggregate_score,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )


class ExperimentComparisonOut(BaseModel):
    experiment: ExperimentOut
    runs: list[RemoteEvalRunSummaryOut]


class ErrorOut(BaseModel):
    type: str
    message: str
