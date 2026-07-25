"""The Celery worker process: defines the app and the one task that
actually delivers a notification.

Each task invocation builds and disposes its own `AsyncEngine` rather than
reusing a cached one — see the Evaluation Engine's `worker.py` for why.
Run this with:

    celery -A notification_service.infrastructure.worker worker -Q q.notification
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from celery import Celery

from notification_service.application.deliver_notification import DeliverNotificationUseCase
from notification_service.infrastructure.config import get_settings
from notification_service.infrastructure.db import build_engine, build_session_factory
from notification_service.infrastructure.repositories import (
    SqlAlchemyNotificationChannelRepository,
    SqlAlchemyNotificationRepository,
)
from notification_service.infrastructure.senders.email_sender import SmtpEmailSender
from notification_service.infrastructure.senders.registry import InMemoryNotificationSenderRegistry
from notification_service.infrastructure.senders.slack_sender import SlackWebhookSender
from notification_service.infrastructure.senders.webhook_sender import GenericWebhookSender

_startup_settings = get_settings()
app = Celery(
    "notification_service", broker=_startup_settings.redis_url, backend=_startup_settings.redis_url
)
app.conf.task_default_queue = "q.notification"


@app.task(name="notification_service.deliver_notification")  # type: ignore[untyped-decorator]
def deliver_notification_task(notification_id: str) -> None:
    asyncio.run(_deliver(notification_id))


async def _deliver(notification_id: str) -> None:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    try:
        session_factory = build_session_factory(engine)
        async with session_factory() as session:
            use_case = DeliverNotificationUseCase(
                notification_repo=SqlAlchemyNotificationRepository(session),
                channel_repo=SqlAlchemyNotificationChannelRepository(session),
                sender_registry=InMemoryNotificationSenderRegistry(
                    [
                        SlackWebhookSender(timeout=settings.upstream_timeout_seconds),
                        GenericWebhookSender(timeout=settings.upstream_timeout_seconds),
                        SmtpEmailSender(
                            host=settings.smtp_host,
                            port=settings.smtp_port,
                            username=settings.smtp_username,
                            password=settings.smtp_password,
                            use_tls=settings.smtp_use_tls,
                            from_address=settings.smtp_from_address,
                        ),
                    ]
                ),
            )
            await use_case.execute(UUID(notification_id))
    finally:
        await engine.dispose()
