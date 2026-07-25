from __future__ import annotations

from typing import Protocol

from trace_collector.domain.entities import Span


class SpanRepository(Protocol):
    async def add_batch(self, spans: list[Span]) -> None: ...

    async def get_by_trace_id(self, trace_id: str) -> list[Span]: ...

    async def list_recent_trace_ids(self, limit: int) -> list[str]:
        """Trace ids ordered by most recent activity (max span end_time)
        first. Deliberately N+1-friendly with `get_by_trace_id` rather than
        a single aggregate query — see the service README for why that's
        an acceptable tradeoff at this stage."""
        ...
