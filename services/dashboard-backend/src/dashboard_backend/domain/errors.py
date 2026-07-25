from __future__ import annotations

from uuid import UUID


class DashboardBackendError(Exception):
    """Base class for all domain errors raised by this service."""


class RunNotFoundError(DashboardBackendError):
    def __init__(self, run_id: UUID) -> None:
        self.run_id = run_id
        super().__init__(f"no eval run {run_id} visible to this credential")


class ReportNotFoundError(DashboardBackendError):
    def __init__(self, report_id: UUID) -> None:
        self.report_id = report_id
        super().__init__(f"no report {report_id} visible to this credential")


class UpstreamServiceError(DashboardBackendError):
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        super().__init__(f"[{service}] {message}")
