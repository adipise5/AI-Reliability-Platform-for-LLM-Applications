from __future__ import annotations

from uuid import UUID

from dashboard_backend.domain.entities import RemoteBaseline
from dashboard_backend.domain.ports import RegressionReader


class GetBaselineUseCase:
    def __init__(self, regression_reader: RegressionReader) -> None:
        self._regression_reader = regression_reader

    async def execute(self, *, credential: str, prompt_id: UUID) -> RemoteBaseline | None:
        return await self._regression_reader.get_baseline(credential, prompt_id)
