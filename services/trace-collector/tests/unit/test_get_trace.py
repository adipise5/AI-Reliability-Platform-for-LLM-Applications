from __future__ import annotations

import pytest

from tests.unit.conftest import FakeSpanRepository
from trace_collector.application.get_trace import GetTraceUseCase
from trace_collector.domain.errors import TraceNotFoundError


async def test_execute_returns_every_span_for_the_trace(span_factory):
    trace_id = "abc123"
    spans = [span_factory(trace_id=trace_id), span_factory(trace_id=trace_id)]
    repo = FakeSpanRepository(seed=spans + [span_factory(trace_id="other-trace")])
    use_case = GetTraceUseCase(repo)

    result = await use_case.execute(trace_id)

    assert {s.span_id for s in result} == {s.span_id for s in spans}


async def test_execute_raises_for_an_unknown_trace():
    use_case = GetTraceUseCase(FakeSpanRepository())

    with pytest.raises(TraceNotFoundError):
        await use_case.execute("nonexistent")
