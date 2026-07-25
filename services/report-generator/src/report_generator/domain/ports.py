"""Ports: interfaces the application layer depends on.

`ExperimentReader` is an HTTP client to Experiment Tracking, modeled as a
port for the same reason a database repository is: the application layer
shouldn't know it's httpx underneath, and a fake makes
`GenerateReportUseCase` testable without that service running.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from report_generator.domain.entities import RemoteExperimentComparison, Report, ReportFormat


class ReportRepository(Protocol):
    async def create(self, report: Report) -> None: ...

    async def get_by_id(self, report_id: UUID) -> Report | None: ...

    async def update(self, report: Report) -> None:
        """Persists the full row — callers read-modify-write via
        `dataclasses.replace`, since `Report` is immutable."""
        ...

    async def list_by_org(
        self, org_id: UUID, *, experiment_id: UUID | None = None
    ) -> list[Report]:
        """Ordered most-recent-first."""
        ...


class ExperimentReader(Protocol):
    async def get_comparison(
        self, credential: str, experiment_id: UUID
    ) -> RemoteExperimentComparison: ...


class ReportRenderer(Protocol):
    format: ReportFormat

    def render(self, comparison: RemoteExperimentComparison) -> bytes:
        """Synchronous and CPU-bound — no I/O, so no reason to make this
        a coroutine."""
        ...


class ReportRendererRegistry(Protocol):
    def get(self, format: ReportFormat) -> ReportRenderer:
        """Raises `report_generator.domain.errors.UnsupportedReportFormatError`
        if `format` isn't registered."""
        ...


class TaskQueue(Protocol):
    def enqueue_generate_report(self, report_id: UUID, credential: str) -> None:
        """`credential` is never persisted to the database — it lives
        only in the queue message. Same JWT-TTL caveat as the Evaluation
        Engine's `TaskQueue.enqueue_run`."""
        ...
