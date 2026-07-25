"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from evaluation_engine.domain.entities import EvalRun, RunItemResult, RunStatus, Score
from evaluation_engine.infrastructure.db import Base
from evaluation_engine.infrastructure.repositories import (
    SqlAlchemyEvalRunRepository,
    SqlAlchemyRunItemResultRepository,
)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"eval_engine": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


def _make_run(**overrides: object) -> EvalRun:
    base = EvalRun(
        id=uuid4(),
        org_id=uuid4(),
        prompt_id=uuid4(),
        prompt_version_id=uuid4(),
        dataset_id=uuid4(),
        model="claude-sonnet-5",
        scorer_names=("exact_match", "llm_judge"),
        status=RunStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    from dataclasses import replace

    return replace(base, **overrides)


async def test_eval_run_repository_create_get_and_update(session):
    repo = SqlAlchemyEvalRunRepository(session)
    run = _make_run()

    await repo.create(run)
    fetched = await repo.get_by_id(run.id)
    assert fetched is not None
    assert fetched.scorer_names == ("exact_match", "llm_judge")
    assert fetched.status == RunStatus.PENDING

    from dataclasses import replace

    updated = replace(
        fetched,
        status=RunStatus.COMPLETED,
        dataset_version=4,
        aggregate_score=0.75,
        completed_at=datetime.now(UTC),
    )
    await repo.update(updated)

    refetched = await repo.get_by_id(run.id)
    assert refetched is not None
    assert refetched.status == RunStatus.COMPLETED
    assert refetched.dataset_version == 4
    assert refetched.aggregate_score == 0.75


async def test_eval_run_repository_list_by_org_filters_and_orders(session):
    repo = SqlAlchemyEvalRunRepository(session)
    org_id = uuid4()
    prompt_id = uuid4()
    older = _make_run(org_id=org_id, prompt_id=prompt_id, created_at=datetime(2026, 1, 1, tzinfo=UTC))
    newer = _make_run(org_id=org_id, prompt_id=prompt_id, created_at=datetime(2026, 2, 1, tzinfo=UTC))
    other_org = _make_run(org_id=uuid4(), prompt_id=prompt_id, created_at=datetime(2026, 3, 1, tzinfo=UTC))
    for run in (older, newer, other_org):
        await repo.create(run)

    results = await repo.list_by_org(org_id)

    assert [r.id for r in results] == [newer.id, older.id]

    filtered = await repo.list_by_org(org_id, prompt_id=prompt_id)
    assert {r.id for r in filtered} == {newer.id, older.id}


async def test_eval_run_repository_get_by_id_returns_none_when_missing(session):
    repo = SqlAlchemyEvalRunRepository(session)

    assert await repo.get_by_id(uuid4()) is None


async def test_run_item_result_repository_create_and_list(session):
    run_repo = SqlAlchemyEvalRunRepository(session)
    item_repo = SqlAlchemyRunItemResultRepository(session)
    run = _make_run()
    await run_repo.create(run)

    result = RunItemResult(
        id=uuid4(),
        run_id=run.id,
        dataset_item_id=uuid4(),
        output="42",
        latency_ms=12.5,
        prompt_tokens=5,
        completion_tokens=1,
        scores=(Score(scorer_name="exact_match", value=1.0, evidence={"expected": "42"}),),
        created_at=datetime.now(UTC),
    )
    await item_repo.create(result)

    listed = await item_repo.list_by_run(run.id)
    assert len(listed) == 1
    assert listed[0].output == "42"
    assert listed[0].scores[0].scorer_name == "exact_match"
    assert listed[0].scores[0].value == 1.0
