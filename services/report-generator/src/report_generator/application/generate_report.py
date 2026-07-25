"""Use case: actually render a report — the work the Celery task
dispatches into.

Failure model mirrors the Evaluation Engine's `ExecuteEvalRunUseCase`:
fail-fast, and any exception marks the report FAILED with the error
recorded before re-raising (so Celery still sees the task as errored).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from report_generator.domain.entities import ReportStatus
from report_generator.domain.ports import ExperimentReader, ReportRendererRegistry, ReportRepository


class GenerateReportUseCase:
    def __init__(
        self,
        report_repo: ReportRepository,
        experiment_reader: ExperimentReader,
        renderer_registry: ReportRendererRegistry,
    ) -> None:
        self._report_repo = report_repo
        self._experiment_reader = experiment_reader
        self._renderer_registry = renderer_registry

    async def execute(self, report_id: UUID, credential: str) -> None:
        report = await self._report_repo.get_by_id(report_id)
        if report is None:
            return

        report = replace(report, status=ReportStatus.GENERATING)
        await self._report_repo.update(report)

        try:
            comparison = await self._experiment_reader.get_comparison(credential, report.experiment_id)
            renderer = self._renderer_registry.get(report.format)
            content = renderer.render(comparison)

            report = replace(
                report,
                status=ReportStatus.READY,
                content=content,
                completed_at=datetime.now(UTC),
            )
            await self._report_repo.update(report)
        except Exception as exc:
            failed = replace(
                report,
                status=ReportStatus.FAILED,
                error_message=str(exc),
                completed_at=datetime.now(UTC),
            )
            await self._report_repo.update(failed)
            raise
