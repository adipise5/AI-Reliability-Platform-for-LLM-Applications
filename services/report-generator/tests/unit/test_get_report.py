from __future__ import annotations

from uuid import uuid4

import pytest

from report_generator.application.get_report import GetReportUseCase
from report_generator.domain.errors import ReportNotFoundError
from tests.unit.conftest import FakeReportRepository, make_report


async def test_returns_report_for_the_owning_org(org_id):
    report = make_report(org_id=org_id)
    repo = FakeReportRepository([report])
    use_case = GetReportUseCase(repo)

    result = await use_case.execute(org_id=org_id, report_id=report.id)

    assert result.id == report.id


async def test_raises_when_missing(org_id):
    repo = FakeReportRepository()
    use_case = GetReportUseCase(repo)

    with pytest.raises(ReportNotFoundError):
        await use_case.execute(org_id=org_id, report_id=uuid4())


async def test_raises_when_report_belongs_to_a_different_org(org_id):
    report = make_report(org_id=uuid4())
    repo = FakeReportRepository([report])
    use_case = GetReportUseCase(repo)

    with pytest.raises(ReportNotFoundError):
        await use_case.execute(org_id=org_id, report_id=report.id)
