from __future__ import annotations

from cost_analytics.application.ingest_usage_event import IngestUsageEventUseCase
from cost_analytics.domain.entities import PricingRate
from tests.unit.conftest import FakePricingTable, FakeUsageRecordRepository


async def test_execute_computes_cost_from_the_pricing_table(org_id):
    repo = FakeUsageRecordRepository()
    pricing = FakePricingTable(PricingRate(prompt_price_per_1k=1.0, completion_price_per_1k=2.0))
    use_case = IngestUsageEventUseCase(repo, pricing)

    record = await use_case.execute(
        org_id=org_id,
        provider="anthropic",
        model="claude-sonnet-5",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    assert record.cost_usd == 1.0 + 1.0  # 1000/1000*1.0 + 500/1000*2.0
    assert repo.records == [record]


async def test_execute_defaults_to_zero_cost_when_no_rate_is_on_file(org_id):
    class NoRatePricingTable:
        def get_rate(self, *, provider, model):
            return None

    use_case = IngestUsageEventUseCase(FakeUsageRecordRepository(), NoRatePricingTable())

    record = await use_case.execute(
        org_id=org_id, provider="unknown", model="mystery-model", prompt_tokens=100, completion_tokens=50
    )

    assert record.cost_usd == 0.0
