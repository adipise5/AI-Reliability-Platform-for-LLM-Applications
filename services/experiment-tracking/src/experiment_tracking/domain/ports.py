from __future__ import annotations

from typing import Protocol
from uuid import UUID

from experiment_tracking.domain.entities import Experiment, RemoteEvalRunSummary


class ExperimentRepository(Protocol):
    async def create(self, experiment: Experiment) -> None: ...

    async def get_by_id(self, experiment_id: UUID) -> Experiment | None: ...

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Experiment | None: ...

    async def add_run(self, experiment_id: UUID, run_id: UUID) -> Experiment:
        """Appends `run_id` (a no-op if already present) and returns the
        updated experiment."""
        ...


class EvalRunReader(Protocol):
    async def get_run(self, credential: str, run_id: UUID) -> RemoteEvalRunSummary:
        """Raises `experiment_tracking.domain.errors.RunNotFoundError` if
        the Evaluation Engine 404s — the run doesn't exist, or doesn't
        belong to this credential's org."""
        ...

    async def list_runs(
        self, credential: str, *, prompt_id: UUID | None = None, dataset_id: UUID | None = None
    ) -> list[RemoteEvalRunSummary]: ...
