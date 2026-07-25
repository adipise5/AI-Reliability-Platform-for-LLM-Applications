"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from dataclasses import replace as dc_replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from prompt_registry.domain.entities import PromotionEvent, Prompt, PromptVersion
from prompt_registry.infrastructure.db import Base
from prompt_registry.infrastructure.repositories import (
    SqlAlchemyPromotionRepository,
    SqlAlchemyPromptRepository,
    SqlAlchemyPromptVersionRepository,
)


def _assert_same_entity(fetched, expected) -> None:
    assert fetched.created_at.replace(tzinfo=None) == expected.created_at.replace(tzinfo=None)
    assert dc_replace(fetched, created_at=expected.created_at) == expected


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"prompt_registry": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_prompt_repository_create_and_lookup(session):
    repo = SqlAlchemyPromptRepository(session)
    org_id = uuid4()
    prompt = Prompt(id=uuid4(), org_id=org_id, name="support-agent", created_at=datetime.now(UTC))

    await repo.create(prompt)

    by_id = await repo.get_by_id(prompt.id)
    by_name = await repo.get_by_org_and_name(org_id, "support-agent")
    assert by_id is not None and by_name is not None
    _assert_same_entity(by_id, prompt)
    _assert_same_entity(by_name, prompt)
    assert await repo.get_by_org_and_name(org_id, "nope") is None


async def test_prompt_version_repository_create_and_list(session):
    prompt_repo = SqlAlchemyPromptRepository(session)
    version_repo = SqlAlchemyPromptVersionRepository(session)
    prompt = Prompt(id=uuid4(), org_id=uuid4(), name="p", created_at=datetime.now(UTC))
    await prompt_repo.create(prompt)
    v1 = PromptVersion(id=uuid4(), prompt_id=prompt.id, template="a", created_at=datetime.now(UTC))
    v2 = PromptVersion(id=uuid4(), prompt_id=prompt.id, template="b", created_at=datetime.now(UTC))
    await version_repo.create(v1)
    await version_repo.create(v2)

    fetched = await version_repo.get_by_id(v1.id)
    assert fetched is not None
    _assert_same_entity(fetched, v1)

    listed = await version_repo.list_by_prompt(prompt.id)
    assert {v.id for v in listed} == {v1.id, v2.id}


async def test_promotion_repository_returns_most_recent(session):
    prompt_repo = SqlAlchemyPromptRepository(session)
    version_repo = SqlAlchemyPromptVersionRepository(session)
    promotion_repo = SqlAlchemyPromotionRepository(session)
    prompt = Prompt(id=uuid4(), org_id=uuid4(), name="p", created_at=datetime.now(UTC))
    await prompt_repo.create(prompt)
    v1 = PromptVersion(id=uuid4(), prompt_id=prompt.id, template="a", created_at=datetime.now(UTC))
    v2 = PromptVersion(id=uuid4(), prompt_id=prompt.id, template="b", created_at=datetime.now(UTC))
    await version_repo.create(v1)
    await version_repo.create(v2)

    await promotion_repo.create(
        PromotionEvent(
            id=uuid4(),
            prompt_id=prompt.id,
            version_id=v1.id,
            environment="prod",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    await promotion_repo.create(
        PromotionEvent(
            id=uuid4(),
            prompt_id=prompt.id,
            version_id=v2.id,
            environment="prod",
            created_at=datetime(2026, 6, 1, tzinfo=UTC),
        )
    )

    active = await promotion_repo.get_active(prompt.id, "prod")
    assert active is not None
    assert active.version_id == v2.id
    assert await promotion_repo.get_active(prompt.id, "staging") is None
