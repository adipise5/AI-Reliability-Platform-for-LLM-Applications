"""The `TaskQueue` port's Celery-backed adapter — used by the FastAPI
process to hand a report off to a worker. The worker side (what actually
runs when the task fires) lives in `infrastructure/worker.py`; this module
only needs the Celery `Task` object to call `.delay()`-equivalent on.
"""

from __future__ import annotations

from uuid import UUID

from celery import Celery


class CeleryTaskQueue:
    def __init__(self, celery_app: Celery) -> None:
        self._celery_app = celery_app

    def enqueue_generate_report(self, report_id: UUID, credential: str) -> None:
        self._celery_app.send_task(
            "report_generator.generate_report", args=[str(report_id), credential]
        )
