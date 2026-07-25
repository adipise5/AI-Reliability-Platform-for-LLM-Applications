from __future__ import annotations

from uuid import UUID

from dashboard_backend.domain.entities import RemoteReport
from dashboard_backend.domain.ports import ReportReader


class ListReportsUseCase:
    def __init__(self, report_reader: ReportReader) -> None:
        self._report_reader = report_reader

    async def execute(
        self, *, credential: str, experiment_id: UUID | None = None
    ) -> list[RemoteReport]:
        return await self._report_reader.list_reports(credential, experiment_id=experiment_id)
