from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from cost_analytics.domain.entities import UsageRecord
from cost_analytics.domain.ports import PricingTable, UsageRecordRepository

_ZERO_RATE_COST = 0.0


class IngestUsageEventUseCase:
    def __init__(self, usage_repo: UsageRecordRepository, pricing_table: PricingTable) -> None:
        self._usage_repo = usage_repo
        self._pricing_table = pricing_table

    async def execute(
        self,
        *,
        org_id: UUID,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> UsageRecord:
        rate = self._pricing_table.get_rate(provider=provider, model=model)
        cost_usd = (
            rate.cost_for(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
            if rate is not None
            else _ZERO_RATE_COST
        )

        record = UsageRecord(
            id=uuid4(),
            org_id=org_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            created_at=datetime.now(UTC),
        )
        await self._usage_repo.create(record)
        return record
