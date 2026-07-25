"""Dependency wiring — see the gateway's api/deps.py for the rationale.

No auth wiring here — see infrastructure/config.py's docstring for why
this service is open in the current MVP.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from trace_collector.application.get_trace import GetTraceUseCase
from trace_collector.application.ingest_spans import IngestSpansUseCase
from trace_collector.application.list_traces import ListTracesUseCase
from trace_collector.domain.ports import SpanRepository
from trace_collector.infrastructure.config import get_settings
from trace_collector.infrastructure.db import build_engine, build_session_factory
from trace_collector.infrastructure.repositories import SqlAlchemySpanRepository


@lru_cache
def _build_engine() -> AsyncEngine:
    return build_engine(get_settings().database_url)


@lru_cache
def _build_session_factory() -> async_sessionmaker[AsyncSession]:
    return build_session_factory(_build_engine())


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _build_session_factory()() as session:
        yield session


def get_span_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> SpanRepository:
    return SqlAlchemySpanRepository(session)


def get_ingest_spans_use_case(
    span_repo: Annotated[SpanRepository, Depends(get_span_repo)],
) -> IngestSpansUseCase:
    return IngestSpansUseCase(span_repo)


def get_get_trace_use_case(
    span_repo: Annotated[SpanRepository, Depends(get_span_repo)],
) -> GetTraceUseCase:
    return GetTraceUseCase(span_repo)


def get_list_traces_use_case(
    span_repo: Annotated[SpanRepository, Depends(get_span_repo)],
) -> ListTracesUseCase:
    return ListTracesUseCase(span_repo)


def reset_cached_singletons() -> None:
    """Test-only hook — see the gateway's equivalent for why."""
    get_settings.cache_clear()
    _build_engine.cache_clear()
    _build_session_factory.cache_clear()
