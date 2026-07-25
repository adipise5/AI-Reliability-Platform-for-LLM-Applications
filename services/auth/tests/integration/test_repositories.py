"""Repository tests against a real (if not Postgres) engine.

Uses SQLite via aiosqlite with a `schema_translate_map` so the same
`auth`-schema-qualified models used against Postgres in production map to
an unqualified in-memory database here — see SQLAlchemy's "schema
translate map" feature. This exercises the actual SQL the repositories
generate, unlike the fakes used everywhere else in the test suite.
"""

from __future__ import annotations

from dataclasses import replace as dc_replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.domain.entities import ApiKey, Org, Role, User
from auth.infrastructure.db import Base
from auth.infrastructure.repositories import (
    SqlAlchemyApiKeyRepository,
    SqlAlchemyOrgRepository,
    SqlAlchemyUserRepository,
)


def _assert_same_entity(fetched, expected) -> None:
    """SQLite (unlike Postgres/asyncpg) doesn't round-trip tzinfo on a
    DateTime(timezone=True) column, so `created_at` comes back naive here
    even though it's a real timestamptz against Postgres. Compare the
    instant separately from everything else instead of penalizing this
    engine-specific quirk in the assertion."""
    assert fetched.created_at.replace(tzinfo=None) == expected.created_at.replace(tzinfo=None)
    assert dc_replace(fetched, created_at=expected.created_at) == expected


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"auth": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_org_repository_create_and_get_round_trip(session):
    repo = SqlAlchemyOrgRepository(session)
    org = Org(id=uuid4(), name="Acme", created_at=datetime.now(UTC))

    await repo.create(org)
    fetched = await repo.get_by_id(org.id)

    assert fetched is not None
    _assert_same_entity(fetched, org)


async def test_org_repository_get_by_id_returns_none_when_missing(session):
    repo = SqlAlchemyOrgRepository(session)

    assert await repo.get_by_id(uuid4()) is None


async def test_user_repository_create_and_lookup_round_trip(session):
    org_repo = SqlAlchemyOrgRepository(session)
    user_repo = SqlAlchemyUserRepository(session)
    org = Org(id=uuid4(), name="Acme", created_at=datetime.now(UTC))
    await org_repo.create(org)
    user = User(
        id=uuid4(),
        org_id=org.id,
        email="owner@acme.example.com",
        password_hash="hashed",
        role=Role.OWNER,
        created_at=datetime.now(UTC),
    )

    await user_repo.create(user)

    fetched_by_id = await user_repo.get_by_id(user.id)
    fetched_by_email = await user_repo.get_by_email("owner@acme.example.com")
    assert fetched_by_id is not None
    assert fetched_by_email is not None
    _assert_same_entity(fetched_by_id, user)
    _assert_same_entity(fetched_by_email, user)
    assert await user_repo.get_by_email("nobody@acme.example.com") is None


async def test_api_key_repository_create_lookup_and_revoke(session):
    org_repo = SqlAlchemyOrgRepository(session)
    key_repo = SqlAlchemyApiKeyRepository(session)
    org = Org(id=uuid4(), name="Acme", created_at=datetime.now(UTC))
    await org_repo.create(org)
    api_key = ApiKey(
        id=uuid4(),
        org_id=org.id,
        name="ci key",
        prefix="arp_live_deadbeef",
        secret_hash="hashed-secret",
        scopes=frozenset({"chat:write"}),
        created_at=datetime.now(UTC),
    )

    await key_repo.create(api_key)
    fetched = await key_repo.get_by_prefix("arp_live_deadbeef")
    assert fetched is not None
    _assert_same_entity(fetched, api_key)
    assert fetched.is_active

    await key_repo.revoke(api_key.id)
    revoked = await key_repo.get_by_id(api_key.id)
    assert revoked is not None
    assert not revoked.is_active
