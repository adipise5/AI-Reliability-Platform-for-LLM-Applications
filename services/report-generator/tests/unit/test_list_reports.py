from __future__ import annotations

from uuid import uuid4

from report_generator.application.list_reports import ListReportsUseCase
from tests.unit.conftest import FakeReportRepository, make_report


async def test_lists_only_reports_for_the_org(org_id):
    mine = make_report(org_id=org_id)
    other = make_report(org_id=uuid4())
    repo = FakeReportRepository([mine, other])
    use_case = ListReportsUseCase(repo)

    reports = await use_case.execute(org_id=org_id)

    assert [r.id for r in reports] == [mine.id]


async def test_filters_by_experiment_id(org_id):
    experiment_id = uuid4()
    matching = make_report(org_id=org_id, experiment_id=experiment_id)
    other = make_report(org_id=org_id, experiment_id=uuid4())
    repo = FakeReportRepository([matching, other])
    use_case = ListReportsUseCase(repo)

    reports = await use_case.execute(org_id=org_id, experiment_id=experiment_id)

    assert [r.id for r in reports] == [matching.id]
