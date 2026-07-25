from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from experiment_tracking.domain.entities import Experiment
from experiment_tracking.domain.errors import DuplicateExperimentNameError
from experiment_tracking.domain.ports import ExperimentRepository


class CreateExperimentUseCase:
    def __init__(self, repo: ExperimentRepository) -> None:
        self._repo = repo

    async def execute(self, *, org_id: UUID, name: str, description: str = "") -> Experiment:
        if await self._repo.get_by_org_and_name(org_id, name) is not None:
            raise DuplicateExperimentNameError(name)

        experiment = Experiment(
            id=uuid4(), org_id=org_id, name=name, description=description, created_at=datetime.now(UTC)
        )
        await self._repo.create(experiment)
        return experiment
