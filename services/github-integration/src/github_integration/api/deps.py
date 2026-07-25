"""Dependency wiring — see the gateway's api/deps.py for the rationale.

The webhook endpoint (`routers/webhooks.py`) deliberately doesn't depend
on `require_principal` — GitHub calls it directly with no bearer token at
all, authenticated instead by the HMAC signature over the payload (see
`domain/webhook_signature.py`). Every other endpoint here is a normal
bearer-authed, org-scoped one.
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

from github_integration.application.complete_check import CompleteCheckUseCase
from github_integration.application.get_check import GetCheckUseCase
from github_integration.application.handle_webhook import HandleWebhookUseCase
from github_integration.application.list_checks import ListChecksUseCase
from github_integration.application.post_pr_comment import PostPrCommentUseCase
from github_integration.domain.ports import CheckRunRepository, GateDecisionReader, GitHubClient
from github_integration.infrastructure.clients.github_client import HttpGitHubClient
from github_integration.infrastructure.clients.regression_detection_client import HttpGateDecisionReader
from github_integration.infrastructure.config import get_settings
from github_integration.infrastructure.db import build_engine, build_session_factory
from github_integration.infrastructure.repositories import SqlAlchemyCheckRunRepository

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


def get_check_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> CheckRunRepository:
    return SqlAlchemyCheckRunRepository(session)


@lru_cache
def _github_client() -> GitHubClient:
    settings = get_settings()
    return HttpGitHubClient(
        settings.github_api_base_url, token=settings.github_token, timeout=settings.upstream_timeout_seconds
    )


@lru_cache
def _gate_decision_reader() -> GateDecisionReader:
    settings = get_settings()
    return HttpGateDecisionReader(
        settings.regression_detection_url, timeout=settings.upstream_timeout_seconds
    )


def get_handle_webhook_use_case(
    check_repo: Annotated[CheckRunRepository, Depends(get_check_repo)],
) -> HandleWebhookUseCase:
    return HandleWebhookUseCase(check_repo, _github_client(), get_settings().github_webhook_secret)


def get_complete_check_use_case(
    check_repo: Annotated[CheckRunRepository, Depends(get_check_repo)],
) -> CompleteCheckUseCase:
    return CompleteCheckUseCase(check_repo, _gate_decision_reader(), _github_client())


def get_post_pr_comment_use_case(
    check_repo: Annotated[CheckRunRepository, Depends(get_check_repo)],
) -> PostPrCommentUseCase:
    return PostPrCommentUseCase(check_repo, _github_client())


def get_get_check_use_case(
    check_repo: Annotated[CheckRunRepository, Depends(get_check_repo)],
) -> GetCheckUseCase:
    return GetCheckUseCase(check_repo)


def get_list_checks_use_case(
    check_repo: Annotated[CheckRunRepository, Depends(get_check_repo)],
) -> ListChecksUseCase:
    return ListChecksUseCase(check_repo)


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
    _github_client.cache_clear()
    _gate_decision_reader.cache_clear()
    _auth_client.cache_clear()
