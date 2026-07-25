from __future__ import annotations

from dashboard_backend.application.list_recent_traces import ListRecentTracesUseCase
from tests.unit.conftest import FakeTraceReader, make_trace


async def test_returns_traces_up_to_the_limit():
    traces = [make_trace() for _ in range(5)]
    use_case = ListRecentTracesUseCase(FakeTraceReader(traces))

    result = await use_case.execute(limit=3)

    assert len(result) == 3
