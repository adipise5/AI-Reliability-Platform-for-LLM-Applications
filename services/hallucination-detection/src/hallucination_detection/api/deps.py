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

from hallucination_detection.application.check_faithfulness import CheckFaithfulnessUseCase
from hallucination_detection.application.get_check import GetCheckUseCase
from hallucination_detection.domain.ports import ClaimExtractor, ClaimVerifier, FaithfulnessCheckRepository
from hallucination_detection.infrastructure.claim_extractor import GatewayClaimExtractor
from hallucination_detection.infrastructure.claim_verifier import GatewayClaimVerifier
from hallucination_detection.infrastructure.config import get_settings
from hallucination_detection.infrastructure.db import build_engine, build_session_factory
from hallucination_detection.infrastructure.gateway_client import HttpGatewayClient
from hallucination_detection.infrastructure.repositories import SqlAlchemyFaithfulnessCheckRepository

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


def get_check_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FaithfulnessCheckRepository:
    return SqlAlchemyFaithfulnessCheckRepository(session)


@lru_cache
def _gateway_client() -> HttpGatewayClient:
    settings = get_settings()
    return HttpGatewayClient(settings.gateway_url, timeout=settings.upstream_timeout_seconds)


@lru_cache
def _claim_extractor() -> ClaimExtractor:
    return GatewayClaimExtractor(_gateway_client())


@lru_cache
def _claim_verifier() -> ClaimVerifier:
    return GatewayClaimVerifier(_gateway_client())


def get_check_faithfulness_use_case(
    repo: Annotated[FaithfulnessCheckRepository, Depends(get_check_repo)],
) -> CheckFaithfulnessUseCase:
    return CheckFaithfulnessUseCase(_claim_extractor(), _claim_verifier(), repo)


def get_get_check_use_case(
    repo: Annotated[FaithfulnessCheckRepository, Depends(get_check_repo)],
) -> GetCheckUseCase:
    return GetCheckUseCase(repo)


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
    _gateway_client.cache_clear()
    _claim_extractor.cache_clear()
    _claim_verifier.cache_clear()
    _auth_client.cache_clear()
