from __future__ import annotations

from trace_collector.domain.entities import Span
from trace_collector.domain.errors import EmptyBatchError
from trace_collector.domain.ports import SpanRepository


class IngestSpansUseCase:
    def __init__(self, span_repo: SpanRepository) -> None:
        self._span_repo = span_repo

    async def execute(self, spans: list[Span]) -> int:
        if not spans:
            raise EmptyBatchError
        await self._span_repo.add_batch(spans)
        return len(spans)
