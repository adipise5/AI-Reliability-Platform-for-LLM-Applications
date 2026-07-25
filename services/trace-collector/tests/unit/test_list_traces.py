from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.unit.conftest import FakeSpanRepository
from trace_collector.application.list_traces import ListTracesUseCase
from trace_collector.domain.entities import SpanStatus


async def test_execute_orders_by_most_recent_activity(span_factory):
    now = datetime.now(UTC)
    older = span_factory(trace_id="older", start_time=now - timedelta(hours=2))
    newer = span_factory(trace_id="newer", start_time=now)
    repo = FakeSpanRepository(seed=[older, newer])
    use_case = ListTracesUseCase(repo)

    summaries = await use_case.execute(limit=20)

    assert [s.trace_id for s in summaries] == ["newer", "older"]


async def test_execute_respects_limit(span_factory):
    repo = FakeSpanRepository(seed=[span_factory(trace_id=f"t{i}") for i in range(5)])
    use_case = ListTracesUseCase(repo)

    summaries = await use_case.execute(limit=2)

    assert len(summaries) == 2


async def test_execute_rolls_up_error_status_from_any_span(span_factory):
    trace_id = "with-error"
    ok_span = span_factory(trace_id=trace_id, status=SpanStatus.OK)
    error_span = span_factory(trace_id=trace_id, status=SpanStatus.ERROR)
    repo = FakeSpanRepository(seed=[ok_span, error_span])
    use_case = ListTracesUseCase(repo)

    summaries = await use_case.execute(limit=20)

    assert summaries[0].status == SpanStatus.ERROR
    assert summaries[0].span_count == 2
