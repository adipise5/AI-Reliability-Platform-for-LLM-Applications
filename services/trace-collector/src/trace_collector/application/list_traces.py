from __future__ import annotations

from trace_collector.domain.entities import TraceSummary
from trace_collector.domain.ports import SpanRepository


class ListTracesUseCase:
    def __init__(self, span_repo: SpanRepository) -> None:
        self._span_repo = span_repo

    async def execute(self, *, limit: int = 20) -> list[TraceSummary]:
        trace_ids = await self._span_repo.list_recent_trace_ids(limit)
        summaries = []
        for trace_id in trace_ids:
            spans = await self._span_repo.get_by_trace_id(trace_id)
            if spans:
                summaries.append(TraceSummary.from_spans(trace_id, spans))
        return summaries
