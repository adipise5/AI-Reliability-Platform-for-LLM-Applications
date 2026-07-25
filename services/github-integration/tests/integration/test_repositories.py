"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from github_integration.domain.entities import CheckConclusion, CheckStatus
from github_integration.infrastructure.db import Base
from github_integration.infrastructure.repositories import SqlAlchemyCheckRunRepository
from tests.unit.conftest import make_check


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"github": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_create_and_get_by_id(session):
    repo = SqlAlchemyCheckRunRepository(session)
    check = make_check()

    await repo.create(check)

    fetched = await repo.get_by_id(check.id)
    assert fetched is not None
    assert fetched.github_check_run_id == check.github_check_run_id
    assert fetched.conclusion is None


async def test_get_by_id_returns_none_when_missing(session):
    repo = SqlAlchemyCheckRunRepository(session)

    assert await repo.get_by_id(uuid4()) is None


async def test_update_persists_conclusion_and_run_id(session):
    repo = SqlAlchemyCheckRunRepository(session)
    check = make_check()
    await repo.create(check)

    run_id = uuid4()
    updated = replace(
        check,
        status=CheckStatus.COMPLETED,
        conclusion=CheckConclusion.SUCCESS,
        run_id=run_id,
    )
    await repo.update(updated)

    fetched = await repo.get_by_id(check.id)
    assert fetched is not None
    assert fetched.status == CheckStatus.COMPLETED
    assert fetched.conclusion == CheckConclusion.SUCCESS
    assert fetched.run_id == run_id


async def test_list_by_org_filters_by_repo_and_commit_sha(session):
    repo = SqlAlchemyCheckRunRepository(session)
    org_id = uuid4()
    matching = make_check(org_id=org_id, repo="acme/widgets", commit_sha="c" * 40)
    other_repo = make_check(org_id=org_id, repo="acme/other", commit_sha="c" * 40)
    other_org = make_check(org_id=uuid4(), repo="acme/widgets", commit_sha="c" * 40)

    for c in (matching, other_repo, other_org):
        await repo.create(c)

    results = await repo.list_by_org(org_id, repo="acme/widgets", commit_sha="c" * 40)

    assert [r.id for r in results] == [matching.id]
