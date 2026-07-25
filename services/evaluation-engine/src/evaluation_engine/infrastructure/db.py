"""Async SQLAlchemy engine/session plumbing. `Base.metadata` is pinned to
the `eval_engine` schema — see ADR-0002.

Unlike every other service's db.py, this one is called both from the
FastAPI process (per-request sessions, engine cached for the process
lifetime) and from Celery task workers, which must build and dispose a
*fresh* engine per task invocation — see `infrastructure/worker.py`'s
module docstring for why an engine can't be cached across `asyncio.run()`
calls.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData(schema="eval_engine")


def build_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def iter_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
