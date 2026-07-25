"""The Celery worker process: defines the app and the one task that
actually renders a report.

Each task invocation builds and disposes its own `AsyncEngine` rather than
reusing a cached one — see the Evaluation Engine's `worker.py` for why
(`asyncio.run()` creates a fresh event loop per call, and a cached engine's
connection pool would be bound to a now-closed loop). Run this with:

    celery -A report_generator.infrastructure.worker worker -Q q.report
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from celery import Celery

from report_generator.application.generate_report import GenerateReportUseCase
from report_generator.infrastructure.clients.experiment_tracking_client import HttpExperimentReader
from report_generator.infrastructure.config import get_settings
from report_generator.infrastructure.db import build_engine, build_session_factory
from report_generator.infrastructure.renderers.html_renderer import HtmlReportRenderer
from report_generator.infrastructure.renderers.pdf_renderer import PdfReportRenderer
from report_generator.infrastructure.renderers.registry import InMemoryReportRendererRegistry
from report_generator.infrastructure.repositories import SqlAlchemyReportRepository

_startup_settings = get_settings()
app = Celery(
    "report_generator", broker=_startup_settings.redis_url, backend=_startup_settings.redis_url
)
app.conf.task_default_queue = "q.report"


@app.task(name="report_generator.generate_report")  # type: ignore[untyped-decorator]
def generate_report_task(report_id: str, credential: str) -> None:
    asyncio.run(_generate(report_id, credential))


async def _generate(report_id: str, credential: str) -> None:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    try:
        session_factory = build_session_factory(engine)
        async with session_factory() as session:
            use_case = GenerateReportUseCase(
                report_repo=SqlAlchemyReportRepository(session),
                experiment_reader=HttpExperimentReader(
                    settings.experiment_tracking_url, timeout=settings.upstream_timeout_seconds
                ),
                renderer_registry=InMemoryReportRendererRegistry(
                    [HtmlReportRenderer(), PdfReportRenderer()]
                ),
            )
            await use_case.execute(UUID(report_id), credential)
    finally:
        await engine.dispose()
