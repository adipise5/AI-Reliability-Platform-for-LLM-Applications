"""Use case: fetch every run in an experiment for side-by-side comparison
— the "prompt x dataset x model" matrix from the original architecture
brief, built by asking the Evaluation Engine for each run rather than
reading a local copy (see ADR-0005)."""

from __future__ import annotations

import asyncio
from uuid import UUID

from experiment_tracking.domain.entities import Experiment, RemoteEvalRunSummary
from experiment_tracking.domain.errors import ExperimentNotFoundError
from experiment_tracking.domain.ports import EvalRunReader, ExperimentRepository


class CompareExperimentUseCase:
    def __init__(self, repo: ExperimentRepository, eval_run_reader: EvalRunReader) -> None:
        self._repo = repo
        self._eval_run_reader = eval_run_reader

    async def execute(
        self, *, org_id: UUID, experiment_id: UUID, credential: str
    ) -> tuple[Experiment, list[RemoteEvalRunSummary]]:
        experiment = await self._repo.get_by_id(experiment_id)
        if experiment is None or experiment.org_id != org_id:
            raise ExperimentNotFoundError(experiment_id)

        if not experiment.run_ids:
            return experiment, []

        runs = await asyncio.gather(
            *(self._eval_run_reader.get_run(credential, run_id) for run_id in experiment.run_ids)
        )
        return experiment, list(runs)
