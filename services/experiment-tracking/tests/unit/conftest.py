from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from experiment_tracking.domain.entities import Experiment, RemoteEvalRunSummary
from experiment_tracking.domain.errors import RunNotFoundError


class FakeExperimentRepository:
    def __init__(self, seed: list[Experiment] | None = None) -> None:
        self.experiments: dict[UUID, Experiment] = {e.id: e for e in (seed or [])}

    async def create(self, experiment: Experiment) -> None:
        self.experiments[experiment.id] = experiment

    async def get_by_id(self, experiment_id: UUID) -> Experiment | None:
        return self.experiments.get(experiment_id)

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Experiment | None:
        return next(
            (e for e in self.experiments.values() if e.org_id == org_id and e.name == name), None
        )

    async def add_run(self, experiment_id: UUID, run_id: UUID) -> Experiment:
        current = self.experiments[experiment_id]
        if run_id not in current.run_ids:
            from dataclasses import replace

            self.experiments[experiment_id] = replace(current, run_ids=(*current.run_ids, run_id))
        return self.experiments[experiment_id]


class FakeEvalRunReader:
    def __init__(self, runs: dict[UUID, RemoteEvalRunSummary] | None = None) -> None:
        self.runs = runs or {}
        self.get_run_calls: list[UUID] = []
        self.list_runs_calls: list[dict[str, object]] = []

    async def get_run(self, credential: str, run_id: UUID) -> RemoteEvalRunSummary:
        self.get_run_calls.append(run_id)
        if run_id not in self.runs:
            raise RunNotFoundError(run_id)
        return self.runs[run_id]

    async def list_runs(
        self, credential: str, *, prompt_id: UUID | None = None, dataset_id: UUID | None = None
    ) -> list[RemoteEvalRunSummary]:
        self.list_runs_calls.append({"prompt_id": prompt_id, "dataset_id": dataset_id})
        matches = list(self.runs.values())
        if prompt_id is not None:
            matches = [r for r in matches if r.prompt_id == prompt_id]
        if dataset_id is not None:
            matches = [r for r in matches if r.dataset_id == dataset_id]
        return matches


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


def make_run_summary(**overrides: object) -> RemoteEvalRunSummary:
    from dataclasses import replace

    base = RemoteEvalRunSummary(
        id=uuid4(),
        prompt_id=uuid4(),
        prompt_version_id=uuid4(),
        dataset_id=uuid4(),
        dataset_version=1,
        model="claude-sonnet-5",
        status="completed",
        aggregate_score=0.9,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    return replace(base, **overrides)
