from __future__ import annotations

from trace_collector.domain.entities import Span
from trace_collector.domain.errors import TraceNotFoundError
from trace_collector.domain.ports import SpanRepository


class GetTraceUseCase:
    def __init__(self, span_repo: SpanRepository) -> None:
        self._span_repo = span_repo

    async def execute(self, trace_id: str) -> list[Span]:
        spans = await self._span_repo.get_by_trace_id(trace_id)
        if not spans:
            raise TraceNotFoundError(trace_id)
        return spans
