from __future__ import annotations

from dashboard_backend.domain.entities import RemoteBudgetStatus
from dashboard_backend.domain.ports import CostReader


class GetBudgetStatusUseCase:
    def __init__(self, cost_reader: CostReader) -> None:
        self._cost_reader = cost_reader

    async def execute(self, *, credential: str) -> RemoteBudgetStatus:
        return await self._cost_reader.get_budget_status(credential)
