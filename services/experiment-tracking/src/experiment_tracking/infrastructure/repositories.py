from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from experiment_tracking.domain.entities import Experiment
from experiment_tracking.infrastructure.models import ExperimentModel


class SqlAlchemyExperimentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, experiment: Experiment) -> None:
        self._session.add(
            ExperimentModel(
                id=experiment.id,
                org_id=experiment.org_id,
                name=experiment.name,
                description=experiment.description,
                run_ids=[str(r) for r in experiment.run_ids],
                created_at=experiment.created_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, experiment_id: UUID) -> Experiment | None:
        model = await self._session.get(ExperimentModel, experiment_id)
        return _to_domain(model) if model else None

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Experiment | None:
        model = await self._session.scalar(
            select(ExperimentModel).where(ExperimentModel.org_id == org_id, ExperimentModel.name == name)
        )
        return _to_domain(model) if model else None

    async def add_run(self, experiment_id: UUID, run_id: UUID) -> Experiment:
        model = await self._session.get(ExperimentModel, experiment_id)
        assert model is not None, "add_run() called for an experiment that doesn't exist"
        run_id_str = str(run_id)
        if run_id_str not in model.run_ids:
            # Reassign (not .append) so SQLAlchemy's change-tracking on the
            # mutable JSON column actually notices the mutation.
            model.run_ids = [*model.run_ids, run_id_str]
            await self._session.commit()
        return _to_domain(model)


def _to_domain(model: ExperimentModel) -> Experiment:
    return Experiment(
        id=model.id,
        org_id=model.org_id,
        name=model.name,
        description=model.description,
        run_ids=tuple(UUID(r) for r in model.run_ids),
        created_at=model.created_at,
    )
