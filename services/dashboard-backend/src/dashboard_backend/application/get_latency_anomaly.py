from __future__ import annotations

from dashboard_backend.domain.entities import RemoteLatencyAnomaly
from dashboard_backend.domain.ports import RegressionReader


class GetLatencyAnomalyUseCase:
    def __init__(self, regression_reader: RegressionReader) -> None:
        self._regression_reader = regression_reader

    async def execute(self) -> RemoteLatencyAnomaly:
        return await self._regression_reader.get_latency_anomaly()
