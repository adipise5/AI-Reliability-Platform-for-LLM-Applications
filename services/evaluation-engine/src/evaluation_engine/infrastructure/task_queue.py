"""The `TaskQueue` port's Celery-backed adapter — used by the FastAPI
process to hand a run off to a worker. The worker side (what actually runs
when the task fires) lives in `infrastructure/worker.py`; this module only
needs the Celery `Task` object to call `.delay()` on.
"""

from __future__ import annotations

from uuid import UUID

from celery import Celery


class CeleryTaskQueue:
    def __init__(self, celery_app: Celery) -> None:
        self._celery_app = celery_app

    def enqueue_run(self, run_id: UUID, credential: str) -> None:
        self._celery_app.send_task("evaluation_engine.execute_run", args=[str(run_id), credential])
