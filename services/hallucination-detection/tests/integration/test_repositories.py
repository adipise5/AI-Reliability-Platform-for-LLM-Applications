"""Repository test against a real (if not Postgres) engine — see the auth
service's test_repositories.py for why SQLite + schema_translate_map is
close enough for CI."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from hallucination_detection.domain.entities import Claim, FaithfulnessCheck, Verdict
from hallucination_detection.infrastructure.db import Base
from hallucination_detection.infrastructure.repositories import SqlAlchemyFaithfulnessCheckRepository


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"hallucination": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_create_and_get_by_id_round_trip(session):
    repo = SqlAlchemyFaithfulnessCheckRepository(session)
    check = FaithfulnessCheck(
        id=uuid4(),
        org_id=uuid4(),
        response="Paris is the capital of France.",
        context="France's capital is Paris.",
        claims=(
            Claim(text="Paris is the capital of France.", verdict=Verdict.SUPPORTED, evidence="matches"),
        ),
        created_at=datetime.now(UTC),
    )

    await repo.create(check)
    fetched = await repo.get_by_id(check.id)

    assert fetched is not None
    assert fetched.response == check.response
    assert fetched.claims[0].verdict == Verdict.SUPPORTED
    assert fetched.faithfulness_score == 1.0


async def test_get_by_id_returns_none_when_missing(session):
    repo = SqlAlchemyFaithfulnessCheckRepository(session)

    assert await repo.get_by_id(uuid4()) is None
