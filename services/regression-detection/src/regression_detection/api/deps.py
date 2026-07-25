"""Dependency wiring — see the gateway's api/deps.py for the rationale.

Gate-decision and baseline endpoints require a principal, since they're
scoped by org. The latency-anomaly check has no org concept at all yet
(it reads the Trace Collector's open query API — see ADR-0004) so it
stays unauthenticated, mirroring the Trace Collector's own access model.
"""

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

from regression_detection.application.check_latency_anomaly import CheckLatencyAnomalyUseCase
from regression_detection.application.evaluate_run import EvaluateRunUseCase
from regression_detection.application.get_baseline import GetBaselineUseCase
from regression_detection.application.get_gate_decision import GetGateDecisionUseCase
from regression_detection.domain.ports import (
    BaselineRepository,
    EvalRunReader,
    GateDecisionRepository,
    TraceReader,
)
from regression_detection.infrastructure.clients.evaluation_engine_client import HttpEvalRunReader
from regression_detection.infrastructure.clients.trace_collector_client import HttpTraceReader
from regression_detection.infrastructure.config import get_settings
from regression_detection.infrastructure.db import build_engine, build_session_factory
from regression_detection.infrastructure.repositories import (
    SqlAlchemyBaselineRepository,
    SqlAlchemyGateDecisionRepository,
)

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


def get_baseline_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> BaselineRepository:
    return SqlAlchemyBaselineRepository(session)


def get_gate_decision_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GateDecisionRepository:
    return SqlAlchemyGateDecisionRepository(session)


@lru_cache
def _eval_run_reader() -> EvalRunReader:
    settings = get_settings()
    return HttpEvalRunReader(settings.evaluation_engine_url, timeout=settings.upstream_timeout_seconds)


@lru_cache
def _trace_reader() -> TraceReader:
    settings = get_settings()
    return HttpTraceReader(settings.trace_collector_url, timeout=settings.upstream_timeout_seconds)


def get_evaluate_run_use_case(
    baseline_repo: Annotated[BaselineRepository, Depends(get_baseline_repo)],
    gate_decision_repo: Annotated[GateDecisionRepository, Depends(get_gate_decision_repo)],
) -> EvaluateRunUseCase:
    settings = get_settings()
    return EvaluateRunUseCase(
        _eval_run_reader(),
        baseline_repo,
        gate_decision_repo,
        fail_threshold_stddev=settings.fail_threshold_stddev,
        review_threshold_stddev=settings.review_threshold_stddev,
    )


def get_get_gate_decision_use_case(
    gate_decision_repo: Annotated[GateDecisionRepository, Depends(get_gate_decision_repo)],
) -> GetGateDecisionUseCase:
    return GetGateDecisionUseCase(gate_decision_repo)


def get_get_baseline_use_case(
    baseline_repo: Annotated[BaselineRepository, Depends(get_baseline_repo)],
) -> GetBaselineUseCase:
    return GetBaselineUseCase(baseline_repo)


def get_check_latency_anomaly_use_case() -> CheckLatencyAnomalyUseCase:
    settings = get_settings()
    return CheckLatencyAnomalyUseCase(
        _trace_reader(),
        stddev_threshold=settings.latency_anomaly_stddev_threshold,
        recent_count=settings.latency_anomaly_recent_count,
        minimum_baseline_size=settings.latency_anomaly_minimum_baseline_size,
    )


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
    _trace_reader.cache_clear()
    _auth_client.cache_clear()
