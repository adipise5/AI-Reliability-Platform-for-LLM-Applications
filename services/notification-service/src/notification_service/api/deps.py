"""Dependency wiring — see the gateway's api/deps.py for the rationale.

Only the FastAPI-process side lives here: request-scoped repos and the
`TaskQueue` port used to hand a notification off. The worker side that
actually delivers it is `infrastructure/worker.py`, wired independently
since it runs in a separate OS process.

Unlike the Evaluation Engine or Report Generator, there's no
`get_bearer_credential` here: delivery never calls back into another ARP
service on the caller's behalf, so there's no credential to forward.
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
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from notification_service.application.create_channel import CreateChannelUseCase
from notification_service.application.delete_channel import DeleteChannelUseCase
from notification_service.application.get_channel import GetChannelUseCase
from notification_service.application.get_notification import GetNotificationUseCase
from notification_service.application.list_channels import ListChannelsUseCase
from notification_service.application.list_notifications import ListNotificationsUseCase
from notification_service.application.send_notification import SendNotificationUseCase
from notification_service.domain.ports import (
    NotificationChannelRepository,
    NotificationRepository,
    TaskQueue,
)
from notification_service.infrastructure.config import get_settings
from notification_service.infrastructure.db import build_engine, build_session_factory
from notification_service.infrastructure.repositories import (
    SqlAlchemyNotificationChannelRepository,
    SqlAlchemyNotificationRepository,
)
from notification_service.infrastructure.task_queue import CeleryTaskQueue


@lru_cache
def _build_engine() -> AsyncEngine:
    return build_engine(get_settings().database_url)


@lru_cache
def _build_session_factory() -> async_sessionmaker[AsyncSession]:
    return build_session_factory(_build_engine())


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _build_session_factory()() as session:
        yield session


def get_channel_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NotificationChannelRepository:
    return SqlAlchemyNotificationChannelRepository(session)


def get_notification_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NotificationRepository:
    return SqlAlchemyNotificationRepository(session)


@lru_cache
def _celery_app() -> Celery:
    settings = get_settings()
    return Celery("notification_service", broker=settings.redis_url, backend=settings.redis_url)


@lru_cache
def _task_queue() -> TaskQueue:
    return CeleryTaskQueue(_celery_app())


def get_create_channel_use_case(
    channel_repo: Annotated[NotificationChannelRepository, Depends(get_channel_repo)],
) -> CreateChannelUseCase:
    return CreateChannelUseCase(channel_repo)


def get_list_channels_use_case(
    channel_repo: Annotated[NotificationChannelRepository, Depends(get_channel_repo)],
) -> ListChannelsUseCase:
    return ListChannelsUseCase(channel_repo)


def get_get_channel_use_case(
    channel_repo: Annotated[NotificationChannelRepository, Depends(get_channel_repo)],
) -> GetChannelUseCase:
    return GetChannelUseCase(channel_repo)


def get_delete_channel_use_case(
    channel_repo: Annotated[NotificationChannelRepository, Depends(get_channel_repo)],
) -> DeleteChannelUseCase:
    return DeleteChannelUseCase(channel_repo)


def get_send_notification_use_case(
    channel_repo: Annotated[NotificationChannelRepository, Depends(get_channel_repo)],
    notification_repo: Annotated[NotificationRepository, Depends(get_notification_repo)],
) -> SendNotificationUseCase:
    return SendNotificationUseCase(channel_repo, notification_repo, _task_queue())


def get_get_notification_use_case(
    notification_repo: Annotated[NotificationRepository, Depends(get_notification_repo)],
) -> GetNotificationUseCase:
    return GetNotificationUseCase(notification_repo)


def get_list_notifications_use_case(
    notification_repo: Annotated[NotificationRepository, Depends(get_notification_repo)],
) -> ListNotificationsUseCase:
    return ListNotificationsUseCase(notification_repo)


@lru_cache
def _auth_client() -> AuthServiceClient:
    settings = get_settings()
    return AuthServiceClient(settings.auth_service_url, timeout=settings.upstream_timeout_seconds)


require_principal = RequirePrincipal(_auth_client())


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
