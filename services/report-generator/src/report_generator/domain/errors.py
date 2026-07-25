from __future__ import annotations

from uuid import UUID


class ReportGeneratorError(Exception):
    """Base class for all domain errors raised by this service."""


class ReportNotFoundError(ReportGeneratorError):
    def __init__(self, report_id: UUID) -> None:
        self.report_id = report_id
        super().__init__(f"no report {report_id} in this org")


class ReportNotReadyError(ReportGeneratorError):
    def __init__(self, report_id: UUID, status: str) -> None:
        self.report_id = report_id
        self.status = status
        super().__init__(f"report {report_id} is not ready yet (status={status})")


class UnsupportedReportFormatError(ReportGeneratorError):
    def __init__(self, format_name: str) -> None:
        self.format_name = format_name
        super().__init__(f"no renderer registered for format {format_name!r}")


class UpstreamServiceError(ReportGeneratorError):
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        super().__init__(f"[{service}] {message}")
