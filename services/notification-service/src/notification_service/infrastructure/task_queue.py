"""The `TaskQueue` port's Celery-backed adapter — used by the FastAPI
process to hand a notification off to a worker. The worker side (what
actually runs when the task fires) lives in `infrastructure/worker.py`.
"""

from __future__ import annotations

from uuid import UUID

from celery import Celery


class CeleryTaskQueue:
    def __init__(self, celery_app: Celery) -> None:
        self._celery_app = celery_app

    def enqueue_deliver_notification(self, notification_id: UUID) -> None:
        self._celery_app.send_task(
            "notification_service.deliver_notification", args=[str(notification_id)]
        )
