from __future__ import annotations

from uuid import uuid4

from dashboard_backend.application.list_reports import ListReportsUseCase
from tests.unit.conftest import FakeReportReader, make_report


async def test_lists_all_reports_without_a_filter():
    reports = [make_report(), make_report()]
    use_case = ListReportsUseCase(FakeReportReader(reports))

    result = await use_case.execute(credential="tok")

    assert len(result) == 2


async def test_filters_by_experiment_id():
    experiment_id = uuid4()
    matching = make_report(experiment_id=experiment_id)
    other = make_report()
    use_case = ListReportsUseCase(FakeReportReader([matching, other]))

    result = await use_case.execute(credential="tok", experiment_id=experiment_id)

    assert [r.id for r in result] == [matching.id]
