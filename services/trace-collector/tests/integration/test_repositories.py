"""Repository test against a real (if not Postgres) engine — see the auth
service's test_repositories.py for why SQLite + schema_translate_map is
close enough for CI."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tests.unit.conftest import make_span
from trace_collector.infrastructure.db import Base
from trace_collector.infrastructure.repositories import SqlAlchemySpanRepository


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"trace_collector": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_add_batch_and_get_by_trace_id(session):
    repo = SqlAlchemySpanRepository(session)
    span_a = make_span(trace_id="trace-a", name="root")
    span_b = make_span(trace_id="trace-a", name="child", parent_span_id=span_a.span_id)
    span_other = make_span(trace_id="trace-b")

    await repo.add_batch([span_a, span_b, span_other])

    fetched = await repo.get_by_trace_id("trace-a")
    assert {s.span_id for s in fetched} == {span_a.span_id, span_b.span_id}
    assert await repo.get_by_trace_id("nonexistent") == []


async def test_list_recent_trace_ids_orders_by_last_activity(session):
    repo = SqlAlchemySpanRepository(session)
    now = datetime.now(UTC)
    await repo.add_batch([make_span(trace_id="older", start_time=now - timedelta(hours=1))])
    await repo.add_batch([make_span(trace_id="newer", start_time=now)])

    recent = await repo.list_recent_trace_ids(limit=10)

    assert recent == ["newer", "older"]


async def test_list_recent_trace_ids_respects_limit(session):
    repo = SqlAlchemySpanRepository(session)
    for i in range(5):
        await repo.add_batch([make_span(trace_id=f"trace-{i}")])

    recent = await repo.list_recent_trace_ids(limit=2)

    assert len(recent) == 2
