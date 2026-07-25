"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from report_generator.domain.entities import ReportStatus
from report_generator.infrastructure.db import Base
from report_generator.infrastructure.repositories import SqlAlchemyReportRepository
from tests.unit.conftest import make_report


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"reports": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_create_and_get_by_id(session):
    repo = SqlAlchemyReportRepository(session)
    report = make_report()

    await repo.create(report)

    fetched = await repo.get_by_id(report.id)
    assert fetched is not None
    assert fetched.status == report.status
    assert fetched.content is None


async def test_get_by_id_returns_none_when_missing(session):
    repo = SqlAlchemyReportRepository(session)

    assert await repo.get_by_id(uuid4()) is None


async def test_update_persists_status_and_content(session):
    repo = SqlAlchemyReportRepository(session)
    report = make_report()
    await repo.create(report)

    updated = replace(report, status=ReportStatus.READY, content=b"rendered-bytes")
    await repo.update(updated)

    fetched = await repo.get_by_id(report.id)
    assert fetched is not None
    assert fetched.status == ReportStatus.READY
    assert fetched.content == b"rendered-bytes"


async def test_list_by_org_orders_most_recent_first_and_filters_by_experiment(session):
    repo = SqlAlchemyReportRepository(session)
    org_id = uuid4()
    experiment_id = uuid4()

    older = make_report(
        org_id=org_id, experiment_id=experiment_id, created_at=datetime.now(UTC) - timedelta(hours=1)
    )
    newer = make_report(org_id=org_id, experiment_id=experiment_id, created_at=datetime.now(UTC))
    other_experiment = make_report(org_id=org_id, created_at=datetime.now(UTC))
    other_org = make_report(org_id=uuid4(), experiment_id=experiment_id)

    for report in (older, newer, other_experiment, other_org):
        await repo.create(report)

    results = await repo.list_by_org(org_id, experiment_id=experiment_id)

    assert [r.id for r in results] == [newer.id, older.id]
