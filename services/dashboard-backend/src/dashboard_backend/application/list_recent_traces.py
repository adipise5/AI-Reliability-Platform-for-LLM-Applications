from __future__ import annotations

from dashboard_backend.domain.entities import RemoteTraceSummary
from dashboard_backend.domain.ports import TraceReader


class ListRecentTracesUseCase:
    def __init__(self, trace_reader: TraceReader) -> None:
        self._trace_reader = trace_reader

    async def execute(self, *, limit: int = 20) -> list[RemoteTraceSummary]:
        return await self._trace_reader.list_recent_traces(limit)
