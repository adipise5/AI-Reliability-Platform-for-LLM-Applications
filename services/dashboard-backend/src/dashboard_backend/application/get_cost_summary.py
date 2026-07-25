from __future__ import annotations

from dashboard_backend.domain.entities import RemoteUsageSummary
from dashboard_backend.domain.ports import CostReader


class GetCostSummaryUseCase:
    def __init__(self, cost_reader: CostReader) -> None:
        self._cost_reader = cost_reader

    async def execute(self, *, credential: str) -> RemoteUsageSummary:
        return await self._cost_reader.get_usage_summary(credential)
