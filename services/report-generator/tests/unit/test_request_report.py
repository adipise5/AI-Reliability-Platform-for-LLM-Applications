from __future__ import annotations

from uuid import uuid4

from report_generator.application.request_report import RequestReportUseCase
from report_generator.domain.entities import ReportFormat, ReportStatus
from tests.unit.conftest import FakeReportRepository, FakeTaskQueue


async def test_creates_a_pending_report_and_enqueues_it(org_id):
    repo = FakeReportRepository()
    queue = FakeTaskQueue()
    use_case = RequestReportUseCase(repo, queue)
    experiment_id = uuid4()

    report = await use_case.execute(
        org_id=org_id, experiment_id=experiment_id, format=ReportFormat.PDF, credential="tok"
    )

    assert report.status == ReportStatus.PENDING
    assert report.experiment_id == experiment_id
    assert report.format == ReportFormat.PDF
    assert repo.reports[report.id] == report
    assert queue.enqueued == [(report.id, "tok")]
