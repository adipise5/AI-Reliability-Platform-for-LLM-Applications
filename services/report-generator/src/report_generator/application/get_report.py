from __future__ import annotations

from uuid import UUID

from report_generator.domain.entities import Report
from report_generator.domain.errors import ReportNotFoundError
from report_generator.domain.ports import ReportRepository


class GetReportUseCase:
    def __init__(self, report_repo: ReportRepository) -> None:
        self._report_repo = report_repo

    async def execute(self, *, org_id: UUID, report_id: UUID) -> Report:
        report = await self._report_repo.get_by_id(report_id)
        if report is None or report.org_id != org_id:
            raise ReportNotFoundError(report_id)
        return report
