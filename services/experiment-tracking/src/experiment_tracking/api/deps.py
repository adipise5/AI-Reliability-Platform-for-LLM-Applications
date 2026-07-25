"""Dependency wiring — see the gateway's api/deps.py for the rationale."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from auth_client import AuthServiceClient
from auth_client.fastapi import RequirePrincipal
from auth_client.models import IntrospectionResult
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from experiment_tracking.application.add_run import AddRunUseCase
from experiment_tracking.application.compare_experiment import CompareExperimentUseCase
from experiment_tracking.application.create_experiment import CreateExperimentUseCase
from experiment_tracking.application.get_experiment import GetExperimentUseCase
from experiment_tracking.application.get_score_history import GetScoreHistoryUseCase
from experiment_tracking.domain.ports import EvalRunReader, ExperimentRepository
from experiment_tracking.infrastructure.clients.evaluation_engine_client import HttpEvalRunReader
from experiment_tracking.infrastructure.config import get_settings
from experiment_tracking.infrastructure.db import build_engine, build_session_factory
from experiment_tracking.infrastructure.repositories import SqlAlchemyExperimentRepository

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


def get_experiment_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExperimentRepository:
    return SqlAlchemyExperimentRepository(session)


@lru_cache
def _eval_run_reader() -> EvalRunReader:
    settings = get_settings()
    return HttpEvalRunReader(settings.evaluation_engine_url, timeout=settings.upstream_timeout_seconds)


def get_create_experiment_use_case(
    repo: Annotated[ExperimentRepository, Depends(get_experiment_repo)],
) -> CreateExperimentUseCase:
    return CreateExperimentUseCase(repo)


def get_add_run_use_case(
    repo: Annotated[ExperimentRepository, Depends(get_experiment_repo)],
) -> AddRunUseCase:
    return AddRunUseCase(repo, _eval_run_reader())


def get_compare_experiment_use_case(
    repo: Annotated[ExperimentRepository, Depends(get_experiment_repo)],
) -> CompareExperimentUseCase:
    return CompareExperimentUseCase(repo, _eval_run_reader())


def get_get_experiment_use_case(
    repo: Annotated[ExperimentRepository, Depends(get_experiment_repo)],
) -> GetExperimentUseCase:
    return GetExperimentUseCase(repo)


def get_score_history_use_case() -> GetScoreHistoryUseCase:
    return GetScoreHistoryUseCase(_eval_run_reader())


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
    _eval_run_reader.cache_clear()
    _auth_client.cache_clear()
