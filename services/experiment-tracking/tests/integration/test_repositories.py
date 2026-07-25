"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment_tracking.domain.entities import Experiment
from experiment_tracking.infrastructure.db import Base
from experiment_tracking.infrastructure.repositories import SqlAlchemyExperimentRepository


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"experiment_tracking": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_create_and_lookup(session):
    repo = SqlAlchemyExperimentRepository(session)
    org_id = uuid4()
    experiment = Experiment(
        id=uuid4(), org_id=org_id, name="rollout-v2", description="d", created_at=datetime.now(UTC)
    )

    await repo.create(experiment)

    by_id = await repo.get_by_id(experiment.id)
    by_name = await repo.get_by_org_and_name(org_id, "rollout-v2")
    assert by_id is not None and by_name is not None
    assert by_id.name == "rollout-v2"
    assert by_name.id == experiment.id
    assert await repo.get_by_org_and_name(org_id, "nope") is None


async def test_add_run_appends_and_is_idempotent(session):
    repo = SqlAlchemyExperimentRepository(session)
    experiment = Experiment(
        id=uuid4(), org_id=uuid4(), name="e", description="", created_at=datetime.now(UTC)
    )
    await repo.create(experiment)
    run_id = uuid4()

    updated = await repo.add_run(experiment.id, run_id)
    assert updated.run_ids == (run_id,)

    updated_again = await repo.add_run(experiment.id, run_id)
    assert updated_again.run_ids == (run_id,)

    refetched = await repo.get_by_id(experiment.id)
    assert refetched is not None
    assert refetched.run_ids == (run_id,)
