from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from cost_analytics.application.get_usage_summary import GetUsageSummaryUseCase
from cost_analytics.domain.entities import UsageRecord
from tests.unit.conftest import FakeUsageRecordRepository


def _record(org_id, provider, model, prompt_tokens, completion_tokens, cost_usd) -> UsageRecord:
    return UsageRecord(
        id=uuid4(),
        org_id=org_id,
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
        created_at=datetime.now(UTC),
    )


async def test_execute_rolls_up_by_provider_and_model(org_id):
    records = [
        _record(org_id, "anthropic", "claude-sonnet-5", 100, 50, 1.0),
        _record(org_id, "anthropic", "claude-sonnet-5", 200, 100, 2.0),
        _record(org_id, "openai", "gpt-5", 100, 50, 0.5),
        _record(uuid4(), "anthropic", "claude-sonnet-5", 999, 999, 99.0),  # different org
    ]
    use_case = GetUsageSummaryUseCase(FakeUsageRecordRepository(seed=records))

    summary = await use_case.execute(org_id=org_id)

    assert summary.total_cost_usd == 3.5
    assert summary.total_prompt_tokens == 400
    assert summary.total_completion_tokens == 200
    assert len(summary.by_model) == 2
    claude_bucket = next(m for m in summary.by_model if m.model == "claude-sonnet-5")
    assert claude_bucket.prompt_tokens == 300
    assert claude_bucket.cost_usd == 3.0


async def test_execute_returns_empty_summary_for_an_org_with_no_usage(org_id):
    use_case = GetUsageSummaryUseCase(FakeUsageRecordRepository())

    summary = await use_case.execute(org_id=org_id)

    assert summary.total_cost_usd == 0
    assert summary.by_model == ()
