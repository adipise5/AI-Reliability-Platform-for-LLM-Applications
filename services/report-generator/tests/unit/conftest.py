from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from report_generator.domain.entities import (
    RemoteExperiment,
    RemoteExperimentComparison,
    RemoteRunSummary,
    Report,
    ReportFormat,
    ReportStatus,
)
from report_generator.domain.errors import UnsupportedReportFormatError, UpstreamServiceError
from report_generator.domain.ports import ReportRenderer


class FakeReportRepository:
    def __init__(self, seed: list[Report] | None = None) -> None:
        self.reports: dict[UUID, Report] = {r.id: r for r in (seed or [])}

    async def create(self, report: Report) -> None:
        self.reports[report.id] = report

    async def get_by_id(self, report_id: UUID) -> Report | None:
        return self.reports.get(report_id)

    async def update(self, report: Report) -> None:
        self.reports[report.id] = report

    async def list_by_org(self, org_id: UUID, *, experiment_id: UUID | None = None) -> list[Report]:
        matches = [r for r in self.reports.values() if r.org_id == org_id]
        if experiment_id is not None:
            matches = [r for r in matches if r.experiment_id == experiment_id]
        return sorted(matches, key=lambda r: r.created_at, reverse=True)


class FakeExperimentReader:
    def __init__(self, comparisons: dict[UUID, RemoteExperimentComparison] | None = None) -> None:
        self.comparisons = comparisons or {}
        self.calls: list[UUID] = []

    async def get_comparison(self, credential: str, experiment_id: UUID) -> RemoteExperimentComparison:
        self.calls.append(experiment_id)
        if experiment_id not in self.comparisons:
            raise UpstreamServiceError("experiment-tracking", f"no experiment {experiment_id}")
        return self.comparisons[experiment_id]


class FakeTaskQueue:
    def __init__(self) -> None:
        self.enqueued: list[tuple[UUID, str]] = []

    def enqueue_generate_report(self, report_id: UUID, credential: str) -> None:
        self.enqueued.append((report_id, credential))


class FakeRenderer:
    def __init__(self, format: ReportFormat, content: bytes = b"rendered", error: Exception | None = None):
        self.format = format
        self._content = content
        self._error = error

    def render(self, comparison: RemoteExperimentComparison) -> bytes:
        if self._error is not None:
            raise self._error
        return self._content


class FakeRendererRegistry:
    def __init__(self, renderers: list[ReportRenderer]) -> None:
        self._renderers = {r.format: r for r in renderers}

    def get(self, format: ReportFormat) -> ReportRenderer:
        renderer = self._renderers.get(format)
        if renderer is None:
            raise UnsupportedReportFormatError(format.value)
        return renderer


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


def make_report(**overrides: object) -> Report:
    base = Report(
        id=uuid4(),
        org_id=uuid4(),
        experiment_id=uuid4(),
        format=ReportFormat.HTML,
        status=ReportStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    return replace(base, **overrides)


def make_comparison(run_count: int = 2, **overrides: object) -> RemoteExperimentComparison:
    experiment = RemoteExperiment(id=uuid4(), name="rollout-v2", description="d", run_ids=())
    runs = tuple(
        RemoteRunSummary(
            id=uuid4(),
            prompt_id=uuid4(),
            model="claude-sonnet-5",
            status="completed",
            aggregate_score=0.9,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        for _ in range(run_count)
    )
    base = RemoteExperimentComparison(experiment=experiment, runs=runs)
    return replace(base, **overrides)
