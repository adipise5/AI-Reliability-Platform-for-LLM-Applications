from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from evaluation_engine.domain.entities import EvalRun, RunItemResult, RunStatus, Score
from evaluation_engine.infrastructure.models import EvalRunModel, RunItemResultModel


class SqlAlchemyEvalRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: EvalRun) -> None:
        self._session.add(_to_model(run))
        await self._session.commit()

    async def get_by_id(self, run_id: UUID) -> EvalRun | None:
        model = await self._session.get(EvalRunModel, run_id)
        return _to_domain(model) if model else None

    async def update(self, run: EvalRun) -> None:
        model = await self._session.get(EvalRunModel, run.id)
        assert model is not None, "update() called for a run that doesn't exist"
        model.dataset_version = run.dataset_version
        model.status = run.status.value
        model.aggregate_score = run.aggregate_score
        model.error_message = run.error_message
        model.completed_at = run.completed_at
        await self._session.commit()

    async def list_by_org(
        self, org_id: UUID, *, prompt_id: UUID | None = None, dataset_id: UUID | None = None
    ) -> list[EvalRun]:
        query = select(EvalRunModel).where(EvalRunModel.org_id == org_id)
        if prompt_id is not None:
            query = query.where(EvalRunModel.prompt_id == prompt_id)
        if dataset_id is not None:
            query = query.where(EvalRunModel.dataset_id == dataset_id)
        query = query.order_by(desc(EvalRunModel.created_at))
        models = await self._session.scalars(query)
        return [_to_domain(m) for m in models]


class SqlAlchemyRunItemResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, result: RunItemResult) -> None:
        self._session.add(
            RunItemResultModel(
                id=result.id,
                run_id=result.run_id,
                dataset_item_id=result.dataset_item_id,
                output=result.output,
                latency_ms=result.latency_ms,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                scores=[
                    {"scorer_name": s.scorer_name, "value": s.value, "evidence": s.evidence}
                    for s in result.scores
                ],
                created_at=result.created_at,
            )
        )
        await self._session.commit()

    async def list_by_run(self, run_id: UUID) -> list[RunItemResult]:
        models = await self._session.scalars(
            select(RunItemResultModel)
            .where(RunItemResultModel.run_id == run_id)
            .order_by(RunItemResultModel.created_at)
        )
        return [_item_to_domain(m) for m in models]


def _to_model(run: EvalRun) -> EvalRunModel:
    return EvalRunModel(
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


def _to_domain(model: EvalRunModel) -> EvalRun:
    return EvalRun(
        id=model.id,
        org_id=model.org_id,
        prompt_id=model.prompt_id,
        prompt_version_id=model.prompt_version_id,
        dataset_id=model.dataset_id,
        dataset_version=model.dataset_version,
        model=model.model,
        scorer_names=tuple(model.scorer_names),
        status=RunStatus(model.status),
        temperature=model.temperature,
        max_tokens=model.max_tokens,
        aggregate_score=model.aggregate_score,
        error_message=model.error_message,
        created_at=model.created_at,
        completed_at=model.completed_at,
    )


def _item_to_domain(model: RunItemResultModel) -> RunItemResult:
    return RunItemResult(
        id=model.id,
        run_id=model.run_id,
        dataset_item_id=model.dataset_item_id,
        output=model.output,
        latency_ms=model.latency_ms,
        prompt_tokens=model.prompt_tokens,
        completion_tokens=model.completion_tokens,
        scores=tuple(
            Score(scorer_name=s["scorer_name"], value=s["value"], evidence=s["evidence"])
            for s in model.scores
        ),
        created_at=model.created_at,
    )
