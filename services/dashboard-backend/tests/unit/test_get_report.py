from __future__ import annotations

from uuid import uuid4

import pytest

from dashboard_backend.application.get_report import GetReportUseCase
from dashboard_backend.domain.errors import ReportNotFoundError
from tests.unit.conftest import FakeReportReader, make_report


async def test_returns_the_report():
    report = make_report()
    use_case = GetReportUseCase(FakeReportReader([report]))

    result = await use_case.execute(credential="tok", report_id=report.id)

    assert result == report


async def test_raises_when_missing():
    use_case = GetReportUseCase(FakeReportReader())

    with pytest.raises(ReportNotFoundError):
        await use_case.execute(credential="tok", report_id=uuid4())
