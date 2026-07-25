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

from dataset_management.application.create_dataset import CreateDatasetUseCase
from dataset_management.application.get_dataset import GetDatasetUseCase
from dataset_management.application.import_items import ImportItemsUseCase
from dataset_management.application.list_items import ListItemsUseCase
from dataset_management.domain.ports import DatasetItemRepository, DatasetRepository
from dataset_management.infrastructure.config import get_settings
from dataset_management.infrastructure.db import build_engine, build_session_factory
from dataset_management.infrastructure.repositories import (
    SqlAlchemyDatasetItemRepository,
    SqlAlchemyDatasetRepository,
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


def get_dataset_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> DatasetRepository:
    return SqlAlchemyDatasetRepository(session)


def get_item_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> DatasetItemRepository:
    return SqlAlchemyDatasetItemRepository(session)


def get_create_dataset_use_case(
    dataset_repo: Annotated[DatasetRepository, Depends(get_dataset_repo)],
) -> CreateDatasetUseCase:
    return CreateDatasetUseCase(dataset_repo)


def get_import_items_use_case(
    dataset_repo: Annotated[DatasetRepository, Depends(get_dataset_repo)],
    item_repo: Annotated[DatasetItemRepository, Depends(get_item_repo)],
) -> ImportItemsUseCase:
    return ImportItemsUseCase(dataset_repo, item_repo)


def get_get_dataset_use_case(
    dataset_repo: Annotated[DatasetRepository, Depends(get_dataset_repo)],
) -> GetDatasetUseCase:
    return GetDatasetUseCase(dataset_repo)


def get_list_items_use_case(
    dataset_repo: Annotated[DatasetRepository, Depends(get_dataset_repo)],
    item_repo: Annotated[DatasetItemRepository, Depends(get_item_repo)],
) -> ListItemsUseCase:
    return ListItemsUseCase(dataset_repo, item_repo)


@lru_cache
def _auth_client() -> AuthServiceClient:
    settings = get_settings()
    return AuthServiceClient(settings.auth_service_url, timeout=settings.auth_service_timeout_seconds)


require_principal = RequirePrincipal(_auth_client())


def org_id_of(principal: IntrospectionResult) -> UUID:
    return UUID(principal.org_id)


def reset_cached_singletons() -> None:
    """Test-only hook — see the gateway's equivalent for why."""
    get_settings.cache_clear()
    _build_engine.cache_clear()
    _build_session_factory.cache_clear()
    _auth_client.cache_clear()
