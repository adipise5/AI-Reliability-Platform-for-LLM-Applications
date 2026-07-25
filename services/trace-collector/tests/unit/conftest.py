from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from trace_collector.domain.entities import Span, SpanStatus


class FakeSpanRepository:
    def __init__(self, seed: list[Span] | None = None) -> None:
        self.spans_by_trace: dict[str, list[Span]] = defaultdict(list)
        for span in seed or []:
            self.spans_by_trace[span.trace_id].append(span)

    async def add_batch(self, spans: list[Span]) -> None:
        for span in spans:
            self.spans_by_trace[span.trace_id].append(span)

    async def get_by_trace_id(self, trace_id: str) -> list[Span]:
        return sorted(self.spans_by_trace.get(trace_id, []), key=lambda s: s.start_time)

    async def list_recent_trace_ids(self, limit: int) -> list[str]:
        def last_end(trace_id: str) -> datetime:
            return max(s.end_time for s in self.spans_by_trace[trace_id])

        return sorted(self.spans_by_trace, key=last_end, reverse=True)[:limit]


def make_span(
    *,
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
    name: str = "gateway.chat",
    status: SpanStatus = SpanStatus.OK,
    start_time: datetime | None = None,
    duration_ms: float = 10.0,
    attributes: dict | None = None,
) -> Span:
    start = start_time or datetime.now(UTC)
    return Span(
        id=str(uuid4()),
        trace_id=trace_id or uuid4().hex,
        span_id=span_id or uuid4().hex[:16],
        parent_span_id=parent_span_id,
        name=name,
        status=status,
        start_time=start,
        end_time=start + timedelta(milliseconds=duration_ms),
        attributes=attributes or {},
    )


@pytest.fixture
def span_factory():
    return make_span
