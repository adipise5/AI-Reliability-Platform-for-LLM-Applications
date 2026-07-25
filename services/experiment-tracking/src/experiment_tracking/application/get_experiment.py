from __future__ import annotations

from uuid import UUID

from experiment_tracking.domain.entities import Experiment
from experiment_tracking.domain.errors import ExperimentNotFoundError
from experiment_tracking.domain.ports import ExperimentRepository


class GetExperimentUseCase:
    def __init__(self, repo: ExperimentRepository) -> None:
        self._repo = repo

    async def execute(self, *, org_id: UUID, experiment_id: UUID) -> Experiment:
        experiment = await self._repo.get_by_id(experiment_id)
        if experiment is None or experiment.org_id != org_id:
            raise ExperimentNotFoundError(experiment_id)
        return experiment
