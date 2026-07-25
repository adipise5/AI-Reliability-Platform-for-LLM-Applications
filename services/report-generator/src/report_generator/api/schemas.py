from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from report_generator.domain.entities import Report, ReportFormat


class RequestReportIn(BaseModel):
    experiment_id: UUID
    format: ReportFormat = ReportFormat.HTML


class ReportOut(BaseModel):
    id: UUID
    org_id: UUID
    experiment_id: UUID
    format: ReportFormat
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, report: Report) -> ReportOut:
        return cls(
            id=report.id,
            org_id=report.org_id,
            experiment_id=report.experiment_id,
            format=report.format,
            status=report.status.value,
            error_message=report.error_message,
            created_at=report.created_at,
            completed_at=report.completed_at,
        )


class ErrorOut(BaseModel):
    type: str
    message: str
