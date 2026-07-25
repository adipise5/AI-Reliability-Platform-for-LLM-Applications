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
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from prompt_registry.application.create_prompt import CreatePromptUseCase
from prompt_registry.application.create_version import CreateVersionUseCase
from prompt_registry.application.diff_versions import DiffVersionsUseCase
from prompt_registry.application.get_active_version import GetActiveVersionUseCase
from prompt_registry.application.get_version import GetVersionUseCase
from prompt_registry.application.promote_version import PromoteVersionUseCase
from prompt_registry.domain.ports import PromotionRepository, PromptRepository, PromptVersionRepository
from prompt_registry.infrastructure.config import get_settings
from prompt_registry.infrastructure.db import build_engine, build_session_factory
from prompt_registry.infrastructure.repositories import (
    SqlAlchemyPromotionRepository,
    SqlAlchemyPromptRepository,
    SqlAlchemyPromptVersionRepository,
)


@lru_cache
def _build_engine() -> AsyncEngine:
    return build_engine(get_settings().database_url)


@lru_cache
def _build_session_factory() -> async_sessionmaker[AsyncSession]:
    return build_session_factory(_build_engine())


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _build_session_factory()() as session:
        yield session


def get_prompt_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> PromptRepository:
    return SqlAlchemyPromptRepository(session)


def get_version_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> PromptVersionRepository:
    return SqlAlchemyPromptVersionRepository(session)


def get_promotion_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> PromotionRepository:
    return SqlAlchemyPromotionRepository(session)


def get_create_prompt_use_case(
    prompt_repo: Annotated[PromptRepository, Depends(get_prompt_repo)],
) -> CreatePromptUseCase:
    return CreatePromptUseCase(prompt_repo)


def get_create_version_use_case(
    prompt_repo: Annotated[PromptRepository, Depends(get_prompt_repo)],
    version_repo: Annotated[PromptVersionRepository, Depends(get_version_repo)],
) -> CreateVersionUseCase:
    return CreateVersionUseCase(prompt_repo, version_repo)


def get_promote_version_use_case(
    prompt_repo: Annotated[PromptRepository, Depends(get_prompt_repo)],
    version_repo: Annotated[PromptVersionRepository, Depends(get_version_repo)],
    promotion_repo: Annotated[PromotionRepository, Depends(get_promotion_repo)],
) -> PromoteVersionUseCase:
    return PromoteVersionUseCase(prompt_repo, version_repo, promotion_repo)


def get_active_version_use_case(
    prompt_repo: Annotated[PromptRepository, Depends(get_prompt_repo)],
    version_repo: Annotated[PromptVersionRepository, Depends(get_version_repo)],
    promotion_repo: Annotated[PromotionRepository, Depends(get_promotion_repo)],
) -> GetActiveVersionUseCase:
    return GetActiveVersionUseCase(prompt_repo, version_repo, promotion_repo)


def get_version_use_case(
    prompt_repo: Annotated[PromptRepository, Depends(get_prompt_repo)],
    version_repo: Annotated[PromptVersionRepository, Depends(get_version_repo)],
) -> GetVersionUseCase:
    return GetVersionUseCase(prompt_repo, version_repo)


def get_diff_versions_use_case(
    prompt_repo: Annotated[PromptRepository, Depends(get_prompt_repo)],
    version_repo: Annotated[PromptVersionRepository, Depends(get_version_repo)],
) -> DiffVersionsUseCase:
    return DiffVersionsUseCase(prompt_repo, version_repo)


@lru_cache
def _auth_client() -> AuthServiceClient:
    settings = get_settings()
    return AuthServiceClient(settings.auth_service_url, timeout=settings.auth_service_timeout_seconds)


# Module-level, deliberately — see libs/auth-client's own test suite for why
# a `Depends(...)` default must reference a name resolvable as a module
# global, not a value built inside a function body.
require_principal = RequirePrincipal(_auth_client())


def org_id_of(principal: IntrospectionResult) -> UUID:
    return UUID(principal.org_id)


def reset_cached_singletons() -> None:
    """Test-only hook — see the gateway's equivalent for why."""
    get_settings.cache_clear()
    _build_engine.cache_clear()
    _build_session_factory.cache_clear()
    _auth_client.cache_clear()
