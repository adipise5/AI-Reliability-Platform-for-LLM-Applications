from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cost_analytics.domain.entities import Budget, UsageRecord
from cost_analytics.infrastructure.models import BudgetModel, UsageRecordModel


class SqlAlchemyUsageRecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: UsageRecord) -> None:
        self._session.add(
            UsageRecordModel(
                id=record.id,
                org_id=record.org_id,
                provider=record.provider,
                model=record.model,
                prompt_tokens=record.prompt_tokens,
                completion_tokens=record.completion_tokens,
                cost_usd=record.cost_usd,
                created_at=record.created_at,
            )
        )
        await self._session.commit()

    async def list_by_org(
        self, org_id: UUID, *, since: datetime | None = None, until: datetime | None = None
    ) -> list[UsageRecord]:
        query = select(UsageRecordModel).where(UsageRecordModel.org_id == org_id)
        if since is not None:
            query = query.where(UsageRecordModel.created_at >= since)
        if until is not None:
            query = query.where(UsageRecordModel.created_at < until)
        models = await self._session.scalars(query.order_by(UsageRecordModel.created_at))
        return [_to_domain(m) for m in models]


class SqlAlchemyBudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, budget: Budget) -> Budget:
        model = await self._session.scalar(
            select(BudgetModel).where(BudgetModel.org_id == budget.org_id)
        )
        if model is None:
            model = BudgetModel(
                id=budget.id,
                org_id=budget.org_id,
                monthly_limit_usd=budget.monthly_limit_usd,
                created_at=budget.created_at,
                updated_at=budget.updated_at,
            )
            self._session.add(model)
        else:
            model.monthly_limit_usd = budget.monthly_limit_usd
            model.updated_at = budget.updated_at
        await self._session.commit()
        return _budget_to_domain(model)

    async def get_by_org(self, org_id: UUID) -> Budget | None:
        model = await self._session.scalar(select(BudgetModel).where(BudgetModel.org_id == org_id))
        return _budget_to_domain(model) if model else None


def _to_domain(model: UsageRecordModel) -> UsageRecord:
    return UsageRecord(
        id=model.id,
        org_id=model.org_id,
        provider=model.provider,
        model=model.model,
        prompt_tokens=model.prompt_tokens,
        completion_tokens=model.completion_tokens,
        cost_usd=model.cost_usd,
        created_at=model.created_at,
    )


def _budget_to_domain(model: BudgetModel) -> Budget:
    return Budget(
        id=model.id,
        org_id=model.org_id,
        monthly_limit_usd=model.monthly_limit_usd,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
