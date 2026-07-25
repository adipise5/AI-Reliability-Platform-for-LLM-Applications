from __future__ import annotations

from uuid import UUID

from report_generator.domain.entities import Report
from report_generator.domain.ports import ReportRepository


class ListReportsUseCase:
    def __init__(self, report_repo: ReportRepository) -> None:
        self._report_repo = report_repo

    async def execute(self, *, org_id: UUID, experiment_id: UUID | None = None) -> list[Report]:
        return await self._report_repo.list_by_org(org_id, experiment_id=experiment_id)
