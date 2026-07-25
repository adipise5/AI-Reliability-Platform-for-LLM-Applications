from __future__ import annotations

from uuid import uuid4

import pytest

from report_generator.application.get_report_content import GetReportContentUseCase
from report_generator.domain.entities import ReportStatus
from report_generator.domain.errors import ReportNotFoundError, ReportNotReadyError
from tests.unit.conftest import FakeReportRepository, make_report


async def test_returns_content_when_ready(org_id):
    report = make_report(org_id=org_id, status=ReportStatus.READY, content=b"hello")
    repo = FakeReportRepository([report])
    use_case = GetReportContentUseCase(repo)

    result = await use_case.execute(org_id=org_id, report_id=report.id)

    assert result.content == b"hello"


async def test_raises_not_ready_when_pending(org_id):
    report = make_report(org_id=org_id, status=ReportStatus.PENDING)
    repo = FakeReportRepository([report])
    use_case = GetReportContentUseCase(repo)

    with pytest.raises(ReportNotReadyError):
        await use_case.execute(org_id=org_id, report_id=report.id)


async def test_raises_not_found_when_missing(org_id):
    repo = FakeReportRepository()
    use_case = GetReportContentUseCase(repo)

    with pytest.raises(ReportNotFoundError):
        await use_case.execute(org_id=org_id, report_id=uuid4())
