"""Use case: roll up an org's usage by model.

Aggregates in Python over every record for the org rather than a SQL
`GROUP BY` — at this stage's expected volume that's a fine tradeoff (same
call made for the Trace Collector's trace summaries), and it keeps the
rollup logic in the domain/application layer instead of a
dialect-specific aggregate query.
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from cost_analytics.domain.entities import ModelUsage, UsageSummary
from cost_analytics.domain.ports import UsageRecordRepository


class GetUsageSummaryUseCase:
    def __init__(self, usage_repo: UsageRecordRepository) -> None:
        self._usage_repo = usage_repo

    async def execute(self, *, org_id: UUID) -> UsageSummary:
        records = await self._usage_repo.list_by_org(org_id)

        totals: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0, 0, 0.0])
        for record in records:
            bucket = totals[(record.provider, record.model)]
            bucket[0] += record.prompt_tokens
            bucket[1] += record.completion_tokens
            bucket[2] += record.cost_usd

        by_model = tuple(
            ModelUsage(
                provider=provider,
                model=model,
                prompt_tokens=int(prompt_tokens),
                completion_tokens=int(completion_tokens),
                cost_usd=cost_usd,
            )
            for (provider, model), (prompt_tokens, completion_tokens, cost_usd) in sorted(totals.items())
        )

        return UsageSummary(
            total_cost_usd=sum(m.cost_usd for m in by_model),
            total_prompt_tokens=sum(m.prompt_tokens for m in by_model),
            total_completion_tokens=sum(m.completion_tokens for m in by_model),
            by_model=by_model,
        )
