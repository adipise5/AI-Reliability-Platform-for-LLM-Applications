from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from report_generator.domain.entities import Report, ReportFormat, ReportStatus
from report_generator.infrastructure.models import ReportModel


class SqlAlchemyReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, report: Report) -> None:
        self._session.add(
            ReportModel(
                id=report.id,
                org_id=report.org_id,
                experiment_id=report.experiment_id,
                format=report.format.value,
                status=report.status.value,
                content=report.content,
                error_message=report.error_message,
                created_at=report.created_at,
                completed_at=report.completed_at,
            )
        )
        await self._session.commit()

    async def get_by_id(self, report_id: UUID) -> Report | None:
        model = await self._session.get(ReportModel, report_id)
        if model is None:
            return None
        return _to_domain(model)

    async def update(self, report: Report) -> None:
        model = await self._session.get(ReportModel, report.id)
        assert model is not None
        model.status = report.status.value
        model.content = report.content
        model.error_message = report.error_message
        model.completed_at = report.completed_at
        await self._session.commit()

    async def list_by_org(
        self, org_id: UUID, *, experiment_id: UUID | None = None
    ) -> list[Report]:
        stmt = select(ReportModel).where(ReportModel.org_id == org_id)
        if experiment_id is not None:
            stmt = stmt.where(ReportModel.experiment_id == experiment_id)
        stmt = stmt.order_by(ReportModel.created_at.desc())
        result = await self._session.scalars(stmt)
        return [_to_domain(model) for model in result]


def _to_domain(model: ReportModel) -> Report:
    return Report(
        id=model.id,
        org_id=model.org_id,
        experiment_id=model.experiment_id,
        format=ReportFormat(model.format),
        status=ReportStatus(model.status),
        content=model.content,
        error_message=model.error_message,
        created_at=model.created_at,
        completed_at=model.completed_at,
    )
