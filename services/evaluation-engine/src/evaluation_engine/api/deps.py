"""Dependency wiring — see the gateway's api/deps.py for the rationale.

Only the FastAPI-process side lives here: request-scoped repos and the
`TaskQueue` port used to hand a run off. The worker side that actually
executes a run is `infrastructure/worker.py`, wired independently since it
runs in a separate OS process — see that module's docstring.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from auth_client import AuthServiceClient
from auth_client.fastapi import RequirePrincipal
from auth_client.models import IntrospectionResult
from celery import Celery
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from evaluation_engine.application.get_run import GetEvalRunUseCase
from evaluation_engine.application.list_runs import ListRunsUseCase
from evaluation_engine.application.trigger_run import TriggerEvalRunUseCase
from evaluation_engine.domain.ports import EvalRunRepository, RunItemResultRepository, TaskQueue
from evaluation_engine.infrastructure.config import get_settings
from evaluation_engine.infrastructure.db import build_engine, build_session_factory
from evaluation_engine.infrastructure.repositories import (
    SqlAlchemyEvalRunRepository,
    SqlAlchemyRunItemResultRepository,
)
from evaluation_engine.infrastructure.task_queue import CeleryTaskQueue

_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _build_engine() -> AsyncEngine:
    return build_engine(get_settings().database_url)


@lru_cache
def _build_session_factory() -> async_sessionmaker[AsyncSession]:
    return build_session_factory(_build_engine())


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _build_session_factory()() as session:
        yield session


def get_eval_run_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> EvalRunRepository:
    return SqlAlchemyEvalRunRepository(session)


def get_item_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> RunItemResultRepository:
    return SqlAlchemyRunItemResultRepository(session)


@lru_cache
def _celery_app() -> Celery:
    settings = get_settings()
    return Celery("evaluation_engine", broker=settings.redis_url, backend=settings.redis_url)


@lru_cache
def _task_queue() -> TaskQueue:
    return CeleryTaskQueue(_celery_app())


def get_trigger_run_use_case(
    eval_run_repo: Annotated[EvalRunRepository, Depends(get_eval_run_repo)],
) -> TriggerEvalRunUseCase:
    return TriggerEvalRunUseCase(eval_run_repo, _task_queue())


def get_get_run_use_case(
    eval_run_repo: Annotated[EvalRunRepository, Depends(get_eval_run_repo)],
    item_repo: Annotated[RunItemResultRepository, Depends(get_item_repo)],
) -> GetEvalRunUseCase:
    return GetEvalRunUseCase(eval_run_repo, item_repo)


def get_list_runs_use_case(
    eval_run_repo: Annotated[EvalRunRepository, Depends(get_eval_run_repo)],
) -> ListRunsUseCase:
    return ListRunsUseCase(eval_run_repo)


@lru_cache
def _auth_client() -> AuthServiceClient:
    settings = get_settings()
    return AuthServiceClient(settings.auth_service_url, timeout=settings.upstream_timeout_seconds)


require_principal = RequirePrincipal(_auth_client())


async def get_bearer_credential(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> str:
    # RequirePrincipal already rejects a missing/invalid token before this
    # runs (both depend on the same header) — this just exposes the raw
    # string for the use case to forward to the task queue.
    assert credentials is not None
    return credentials.credentials


def org_id_of(principal: IntrospectionResult) -> UUID:
    return UUID(principal.org_id)


def reset_cached_singletons() -> None:
    """Test-only hook — see the gateway's equivalent for why."""
    get_settings.cache_clear()
    _build_engine.cache_clear()
    _build_session_factory.cache_clear()
    _celery_app.cache_clear()
    _task_queue.cache_clear()
    _auth_client.cache_clear()
