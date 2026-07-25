from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from cost_analytics.application.get_budget_status import GetBudgetStatusUseCase
from cost_analytics.domain.entities import Budget, UsageRecord
from tests.unit.conftest import FakeBudgetRepository, FakeUsageRecordRepository


def _record(org_id, cost_usd, *, when) -> UsageRecord:
    return UsageRecord(
        id=uuid4(),
        org_id=org_id,
        provider="anthropic",
        model="m",
        prompt_tokens=1,
        completion_tokens=1,
        cost_usd=cost_usd,
        created_at=when,
    )


async def test_execute_reports_no_limit_when_no_budget_is_set(org_id):
    now = datetime.now(UTC)
    usage_repo = FakeUsageRecordRepository(seed=[_record(org_id, 5.0, when=now)])
    use_case = GetBudgetStatusUseCase(FakeBudgetRepository(), usage_repo)

    status = await use_case.execute(org_id=org_id)

    assert status.limit_usd is None
    assert status.remaining_usd is None
    assert status.over_budget is False
    assert status.spent_this_month_usd == 5.0


async def test_execute_reports_under_budget(org_id):
    now = datetime.now(UTC)
    budget = Budget(id=uuid4(), org_id=org_id, monthly_limit_usd=100.0, created_at=now, updated_at=now)
    usage_repo = FakeUsageRecordRepository(seed=[_record(org_id, 30.0, when=now)])
    use_case = GetBudgetStatusUseCase(FakeBudgetRepository(seed=[budget]), usage_repo)

    status = await use_case.execute(org_id=org_id)

    assert status.limit_usd == 100.0
    assert status.remaining_usd == 70.0
    assert status.over_budget is False


async def test_execute_reports_over_budget(org_id):
    now = datetime.now(UTC)
    budget = Budget(id=uuid4(), org_id=org_id, monthly_limit_usd=10.0, created_at=now, updated_at=now)
    usage_repo = FakeUsageRecordRepository(seed=[_record(org_id, 15.0, when=now)])
    use_case = GetBudgetStatusUseCase(FakeBudgetRepository(seed=[budget]), usage_repo)

    status = await use_case.execute(org_id=org_id)

    assert status.remaining_usd == -5.0
    assert status.over_budget is True


async def test_execute_excludes_usage_from_before_this_month(org_id):
    now = datetime.now(UTC)
    last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    usage_repo = FakeUsageRecordRepository(
        seed=[_record(org_id, 50.0, when=last_month), _record(org_id, 5.0, when=now)]
    )
    use_case = GetBudgetStatusUseCase(FakeBudgetRepository(), usage_repo)

    status = await use_case.execute(org_id=org_id)

    assert status.spent_this_month_usd == 5.0
