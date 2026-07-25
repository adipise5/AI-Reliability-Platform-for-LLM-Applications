from __future__ import annotations

import pytest

from tests.unit.conftest import FakeSpanRepository
from trace_collector.application.ingest_spans import IngestSpansUseCase
from trace_collector.domain.errors import EmptyBatchError


async def test_execute_stores_all_spans_and_returns_the_count(span_factory):
    repo = FakeSpanRepository()
    use_case = IngestSpansUseCase(repo)
    spans = [span_factory(), span_factory()]

    count = await use_case.execute(spans)

    assert count == 2
    assert sum(len(v) for v in repo.spans_by_trace.values()) == 2


async def test_execute_rejects_an_empty_batch():
    use_case = IngestSpansUseCase(FakeSpanRepository())

    with pytest.raises(EmptyBatchError):
        await use_case.execute([])
