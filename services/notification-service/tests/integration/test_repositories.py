"""Repository tests against a real (if not Postgres) engine — see the
auth service's test_repositories.py for why SQLite + schema_translate_map
is close enough for CI."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from notification_service.domain.entities import NotificationStatus
from notification_service.infrastructure.db import Base
from notification_service.infrastructure.repositories import (
    SqlAlchemyNotificationChannelRepository,
    SqlAlchemyNotificationRepository,
)
from tests.unit.conftest import make_channel, make_notification


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:").execution_options(
        schema_translate_map={"notifications": None}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


async def test_channel_create_and_get_by_id(session):
    repo = SqlAlchemyNotificationChannelRepository(session)
    channel = make_channel()

    await repo.create(channel)

    fetched = await repo.get_by_id(channel.id)
    assert fetched is not None
    assert fetched.target == channel.target


async def test_channel_list_by_org_and_delete(session):
    repo = SqlAlchemyNotificationChannelRepository(session)
    org_id = uuid4()
    mine = make_channel(org_id=org_id)
    other = make_channel(org_id=uuid4())
    await repo.create(mine)
    await repo.create(other)

    listed = await repo.list_by_org(org_id)
    assert [c.id for c in listed] == [mine.id]

    await repo.delete(mine.id)
    assert await repo.get_by_id(mine.id) is None


async def test_notification_create_update_and_list(session):
    channel_repo = SqlAlchemyNotificationChannelRepository(session)
    notification_repo = SqlAlchemyNotificationRepository(session)
    channel = make_channel()
    await channel_repo.create(channel)

    notification = make_notification(org_id=channel.org_id, channel_id=channel.id)
    await notification_repo.create(notification)

    fetched = await notification_repo.get_by_id(notification.id)
    assert fetched is not None
    assert fetched.status == NotificationStatus.PENDING

    updated = replace(
        notification, status=NotificationStatus.SENT, error_message=None
    )
    await notification_repo.update(updated)

    refetched = await notification_repo.get_by_id(notification.id)
    assert refetched is not None
    assert refetched.status == NotificationStatus.SENT

    listed = await notification_repo.list_by_org(channel.org_id, channel_id=channel.id)
    assert [n.id for n in listed] == [notification.id]
