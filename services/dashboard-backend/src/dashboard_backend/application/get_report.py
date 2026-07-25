from __future__ import annotations

from uuid import UUID

from dashboard_backend.domain.entities import RemoteReport
from dashboard_backend.domain.ports import ReportReader


class GetReportUseCase:
    def __init__(self, report_reader: ReportReader) -> None:
        self._report_reader = report_reader

    async def execute(self, *, credential: str, report_id: UUID) -> RemoteReport:
        return await self._report_reader.get_report(credential, report_id)
