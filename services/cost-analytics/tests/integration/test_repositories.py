"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from cost_analytics.domain.entities import Budget, UsageRecord
from cost_analytics.infrastructure.db import Base
from cost_analytics.infrastructure.repositories import (
    SqlAlchemyBudgetRepository,
    SqlAlchemyUsageRecordRepository,
)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"cost_analytics": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_usage_record_repository_create_and_list_with_date_filters(session):
    repo = SqlAlchemyUsageRecordRepository(session)
    org_id = uuid4()
    now = datetime.now(UTC)
    older = UsageRecord(
        id=uuid4(), org_id=org_id, provider="anthropic", model="m", prompt_tokens=1,
        completion_tokens=1, cost_usd=1.0, created_at=now - timedelta(days=40),
    )
    newer = UsageRecord(
        id=uuid4(), org_id=org_id, provider="anthropic", model="m", prompt_tokens=2,
        completion_tokens=2, cost_usd=2.0, created_at=now,
    )
    await repo.create(older)
    await repo.create(newer)

    all_records = await repo.list_by_org(org_id)
    assert {r.id for r in all_records} == {older.id, newer.id}

    recent_only = await repo.list_by_org(org_id, since=now - timedelta(days=1))
    assert [r.id for r in recent_only] == [newer.id]


async def test_budget_repository_upsert_and_get(session):
    repo = SqlAlchemyBudgetRepository(session)
    org_id = uuid4()
    now = datetime.now(UTC)
    budget = Budget(id=uuid4(), org_id=org_id, monthly_limit_usd=100.0, created_at=now, updated_at=now)

    created = await repo.upsert(budget)
    assert created.monthly_limit_usd == 100.0

    later = now + timedelta(hours=1)
    updated_budget = Budget(
        id=uuid4(), org_id=org_id, monthly_limit_usd=200.0, created_at=later, updated_at=later
    )
    updated = await repo.upsert(updated_budget)

    assert updated.monthly_limit_usd == 200.0
    fetched = await repo.get_by_org(org_id)
    assert fetched is not None
    assert fetched.monthly_limit_usd == 200.0

    assert await repo.get_by_org(uuid4()) is None
