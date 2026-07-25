"""Dependency wiring — see the gateway's api/deps.py for the rationale.

Only the FastAPI-process side lives here: request-scoped repos and the
`TaskQueue` port used to hand a report off. The worker side that actually
renders a report is `infrastructure/worker.py`, wired independently since
it runs in a separate OS process — see that module's docstring.
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

from report_generator.application.get_report import GetReportUseCase
from report_generator.application.get_report_content import GetReportContentUseCase
from report_generator.application.list_reports import ListReportsUseCase
from report_generator.application.request_report import RequestReportUseCase
from report_generator.domain.ports import ReportRepository, TaskQueue
from report_generator.infrastructure.config import get_settings
from report_generator.infrastructure.db import build_engine, build_session_factory
from report_generator.infrastructure.repositories import SqlAlchemyReportRepository
from report_generator.infrastructure.task_queue import CeleryTaskQueue

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


def get_report_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> ReportRepository:
    return SqlAlchemyReportRepository(session)


@lru_cache
def _celery_app() -> Celery:
    settings = get_settings()
    return Celery("report_generator", broker=settings.redis_url, backend=settings.redis_url)


@lru_cache
def _task_queue() -> TaskQueue:
    return CeleryTaskQueue(_celery_app())


def get_request_report_use_case(
    report_repo: Annotated[ReportRepository, Depends(get_report_repo)],
) -> RequestReportUseCase:
    return RequestReportUseCase(report_repo, _task_queue())


def get_get_report_use_case(
    report_repo: Annotated[ReportRepository, Depends(get_report_repo)],
) -> GetReportUseCase:
    return GetReportUseCase(report_repo)


def get_list_reports_use_case(
    report_repo: Annotated[ReportRepository, Depends(get_report_repo)],
) -> ListReportsUseCase:
    return ListReportsUseCase(report_repo)


def get_get_report_content_use_case(
    report_repo: Annotated[ReportRepository, Depends(get_report_repo)],
) -> GetReportContentUseCase:
    return GetReportContentUseCase(report_repo)


@lru_cache
def _auth_client() -> AuthServiceClient:
    settings = get_settings()
    return AuthServiceClient(settings.auth_service_url, timeout=settings.upstream_timeout_seconds)


require_principal = RequirePrincipal(_auth_client())


async def get_bearer_credential(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> str:
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
