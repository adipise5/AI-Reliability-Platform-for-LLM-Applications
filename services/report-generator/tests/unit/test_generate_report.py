from __future__ import annotations

from uuid import uuid4

import pytest

from report_generator.application.generate_report import GenerateReportUseCase
from report_generator.domain.entities import ReportFormat, ReportStatus
from report_generator.domain.errors import UpstreamServiceError
from tests.unit.conftest import (
    FakeExperimentReader,
    FakeRenderer,
    FakeRendererRegistry,
    FakeReportRepository,
    make_comparison,
    make_report,
)


async def test_missing_report_is_a_noop():
    repo = FakeReportRepository()
    use_case = GenerateReportUseCase(repo, FakeExperimentReader(), FakeRendererRegistry([]))

    await use_case.execute(uuid4(), "tok")  # should not raise


async def test_renders_and_marks_ready():
    report = make_report(format=ReportFormat.HTML)
    repo = FakeReportRepository([report])
    comparison = make_comparison()
    reader = FakeExperimentReader({report.experiment_id: comparison})
    registry = FakeRendererRegistry([FakeRenderer(ReportFormat.HTML, content=b"<html>ok</html>")])
    use_case = GenerateReportUseCase(repo, reader, registry)

    await use_case.execute(report.id, "tok")

    updated = repo.reports[report.id]
    assert updated.status == ReportStatus.READY
    assert updated.content == b"<html>ok</html>"
    assert updated.completed_at is not None
    assert reader.calls == [report.experiment_id]


async def test_marks_failed_and_reraises_on_upstream_error():
    report = make_report(format=ReportFormat.HTML)
    repo = FakeReportRepository([report])
    reader = FakeExperimentReader({})  # experiment_id not registered -> raises
    registry = FakeRendererRegistry([FakeRenderer(ReportFormat.HTML)])
    use_case = GenerateReportUseCase(repo, reader, registry)

    with pytest.raises(UpstreamServiceError):
        await use_case.execute(report.id, "tok")

    updated = repo.reports[report.id]
    assert updated.status == ReportStatus.FAILED
    assert updated.error_message is not None
    assert updated.completed_at is not None


async def test_marks_failed_and_reraises_on_render_error():
    report = make_report(format=ReportFormat.PDF)
    repo = FakeReportRepository([report])
    comparison = make_comparison()
    reader = FakeExperimentReader({report.experiment_id: comparison})
    registry = FakeRendererRegistry(
        [FakeRenderer(ReportFormat.PDF, error=RuntimeError("boom"))]
    )
    use_case = GenerateReportUseCase(repo, reader, registry)

    with pytest.raises(RuntimeError):
        await use_case.execute(report.id, "tok")

    updated = repo.reports[report.id]
    assert updated.status == ReportStatus.FAILED
    assert updated.error_message == "boom"
