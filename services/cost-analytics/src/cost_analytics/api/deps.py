"""Dependency wiring — see the gateway's api/deps.py for the rationale.

No auth on the ingestion path — see infrastructure/config.py's docstring
for why. The read endpoints (usage summary, budget) do require a
principal, since this service tracks real per-tenant financial data.
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
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from cost_analytics.application.get_budget_status import GetBudgetStatusUseCase
from cost_analytics.application.get_usage_summary import GetUsageSummaryUseCase
from cost_analytics.application.ingest_usage_event import IngestUsageEventUseCase
from cost_analytics.application.set_budget import SetBudgetUseCase
from cost_analytics.domain.ports import BudgetRepository, PricingTable, UsageRecordRepository
from cost_analytics.infrastructure.config import get_settings
from cost_analytics.infrastructure.db import build_engine, build_session_factory
from cost_analytics.infrastructure.pricing import StaticPricingTable
from cost_analytics.infrastructure.repositories import (
    SqlAlchemyBudgetRepository,
    SqlAlchemyUsageRecordRepository,
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


def get_usage_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> UsageRecordRepository:
    return SqlAlchemyUsageRecordRepository(session)


def get_budget_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> BudgetRepository:
    return SqlAlchemyBudgetRepository(session)


@lru_cache
def _pricing_table() -> PricingTable:
    return StaticPricingTable()


def get_pricing_table() -> PricingTable:
    return _pricing_table()


def get_ingest_usage_event_use_case(
    usage_repo: Annotated[UsageRecordRepository, Depends(get_usage_repo)],
    pricing_table: Annotated[PricingTable, Depends(get_pricing_table)],
) -> IngestUsageEventUseCase:
    return IngestUsageEventUseCase(usage_repo, pricing_table)


def get_usage_summary_use_case(
    usage_repo: Annotated[UsageRecordRepository, Depends(get_usage_repo)],
) -> GetUsageSummaryUseCase:
    return GetUsageSummaryUseCase(usage_repo)


def get_set_budget_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repo)],
) -> SetBudgetUseCase:
    return SetBudgetUseCase(budget_repo)


def get_budget_status_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repo)],
    usage_repo: Annotated[UsageRecordRepository, Depends(get_usage_repo)],
) -> GetBudgetStatusUseCase:
    return GetBudgetStatusUseCase(budget_repo, usage_repo)


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
    _pricing_table.cache_clear()
    _auth_client.cache_clear()
