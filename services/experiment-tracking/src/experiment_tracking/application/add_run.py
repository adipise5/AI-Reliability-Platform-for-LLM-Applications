"""Use case: attach an eval run to an experiment.

Confirms the run is real (and visible to this credential) by asking the
Evaluation Engine before recording it — an experiment full of run ids that
don't resolve to anything would be useless."""

from __future__ import annotations

from uuid import UUID

from experiment_tracking.domain.entities import Experiment
from experiment_tracking.domain.errors import ExperimentNotFoundError
from experiment_tracking.domain.ports import EvalRunReader, ExperimentRepository


class AddRunUseCase:
    def __init__(self, repo: ExperimentRepository, eval_run_reader: EvalRunReader) -> None:
        self._repo = repo
        self._eval_run_reader = eval_run_reader

    async def execute(
        self, *, org_id: UUID, experiment_id: UUID, run_id: UUID, credential: str
    ) -> Experiment:
        experiment = await self._repo.get_by_id(experiment_id)
        if experiment is None or experiment.org_id != org_id:
            raise ExperimentNotFoundError(experiment_id)

        await self._eval_run_reader.get_run(credential, run_id)  # raises RunNotFoundError if invalid

        return await self._repo.add_run(experiment_id, run_id)
