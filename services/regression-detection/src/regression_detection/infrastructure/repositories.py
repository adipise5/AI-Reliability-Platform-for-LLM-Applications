from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from regression_detection.domain.entities import Baseline, GateDecision, GateVerdict
from regression_detection.infrastructure.models import BaselineModel, GateDecisionModel


class SqlAlchemyBaselineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, baseline: Baseline) -> Baseline:
        existing = await self._session.scalar(
            select(BaselineModel).where(
                BaselineModel.org_id == baseline.org_id,
                BaselineModel.prompt_id == baseline.prompt_id,
            )
        )
        if existing is None:
            self._session.add(
                BaselineModel(
                    id=baseline.id,
                    org_id=baseline.org_id,
                    prompt_id=baseline.prompt_id,
                    mean_score=baseline.mean_score,
                    stddev_score=baseline.stddev_score,
                    sample_size=baseline.sample_size,
                    updated_at=baseline.updated_at,
                )
            )
        else:
            existing.mean_score = baseline.mean_score
            existing.stddev_score = baseline.stddev_score
            existing.sample_size = baseline.sample_size
            existing.updated_at = baseline.updated_at
        await self._session.commit()
        return baseline

    async def get_by_prompt(self, org_id: UUID, prompt_id: UUID) -> Baseline | None:
        model = await self._session.scalar(
            select(BaselineModel).where(
                BaselineModel.org_id == org_id,
                BaselineModel.prompt_id == prompt_id,
            )
        )
        if model is None:
            return None
        return _to_baseline(model)


class SqlAlchemyGateDecisionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, decision: GateDecision) -> None:
        self._session.add(
            GateDecisionModel(
                id=decision.id,
                org_id=decision.org_id,
                prompt_id=decision.prompt_id,
                run_id=decision.run_id,
                observed_score=decision.observed_score,
                baseline_mean=decision.baseline_mean,
                baseline_stddev=decision.baseline_stddev,
                verdict=decision.verdict.value,
                created_at=decision.created_at,
            )
        )
        await self._session.commit()

    async def get_latest_for_run(self, run_id: UUID) -> GateDecision | None:
        model = await self._session.scalar(
            select(GateDecisionModel)
            .where(GateDecisionModel.run_id == run_id)
            .order_by(GateDecisionModel.created_at.desc())
            .limit(1)
        )
        if model is None:
            return None
        return _to_gate_decision(model)


def _to_baseline(model: BaselineModel) -> Baseline:
    return Baseline(
        id=model.id,
        org_id=model.org_id,
        prompt_id=model.prompt_id,
        mean_score=model.mean_score,
        stddev_score=model.stddev_score,
        sample_size=model.sample_size,
        updated_at=model.updated_at,
    )


def _to_gate_decision(model: GateDecisionModel) -> GateDecision:
    return GateDecision(
        id=model.id,
        org_id=model.org_id,
        prompt_id=model.prompt_id,
        run_id=model.run_id,
        observed_score=model.observed_score,
        baseline_mean=model.baseline_mean,
        baseline_stddev=model.baseline_stddev,
        verdict=GateVerdict(model.verdict),
        created_at=model.created_at,
    )
