"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from regression_detection.domain.entities import Baseline, GateDecision, GateVerdict
from regression_detection.infrastructure.db import Base
from regression_detection.infrastructure.repositories import (
    SqlAlchemyBaselineRepository,
    SqlAlchemyGateDecisionRepository,
)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"regression": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_baseline_upsert_creates_then_updates(session):
    repo = SqlAlchemyBaselineRepository(session)
    org_id, prompt_id = uuid4(), uuid4()
    first = Baseline(
        id=uuid4(),
        org_id=org_id,
        prompt_id=prompt_id,
        mean_score=0.9,
        stddev_score=0.0,
        sample_size=1,
        updated_at=datetime.now(UTC),
    )

    await repo.upsert(first)
    stored = await repo.get_by_prompt(org_id, prompt_id)
    assert stored is not None
    assert stored.sample_size == 1

    second = Baseline(
        id=uuid4(),
        org_id=org_id,
        prompt_id=prompt_id,
        mean_score=0.85,
        stddev_score=0.05,
        sample_size=2,
        updated_at=datetime.now(UTC),
    )
    await repo.upsert(second)

    updated = await repo.get_by_prompt(org_id, prompt_id)
    assert updated is not None
    assert updated.sample_size == 2
    assert updated.mean_score == 0.85


async def test_baseline_get_by_prompt_returns_none_when_missing(session):
    repo = SqlAlchemyBaselineRepository(session)

    assert await repo.get_by_prompt(uuid4(), uuid4()) is None


async def test_gate_decision_create_is_append_only_and_latest_wins(session):
    repo = SqlAlchemyGateDecisionRepository(session)
    org_id, prompt_id, run_id = uuid4(), uuid4(), uuid4()

    first = GateDecision(
        id=uuid4(),
        org_id=org_id,
        prompt_id=prompt_id,
        run_id=run_id,
        observed_score=0.9,
        baseline_mean=0.9,
        baseline_stddev=0.0,
        verdict=GateVerdict.PASS,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    second = GateDecision(
        id=uuid4(),
        org_id=org_id,
        prompt_id=prompt_id,
        run_id=run_id,
        observed_score=0.5,
        baseline_mean=0.9,
        baseline_stddev=0.05,
        verdict=GateVerdict.FAIL,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )

    await repo.create(first)
    await repo.create(second)

    latest = await repo.get_latest_for_run(run_id)
    assert latest is not None
    assert latest.id == second.id
    assert latest.verdict == GateVerdict.FAIL


async def test_gate_decision_get_latest_for_run_returns_none_when_missing(session):
    repo = SqlAlchemyGateDecisionRepository(session)

    assert await repo.get_latest_for_run(uuid4()) is None
