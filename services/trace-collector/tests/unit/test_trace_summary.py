from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.unit.conftest import make_span
from trace_collector.domain.entities import SpanStatus, TraceSummary


def test_from_spans_uses_the_parentless_span_as_root():
    now = datetime.now(UTC)
    root = make_span(trace_id="t1", parent_span_id=None, name="gateway.chat", start_time=now)
    child = make_span(
        trace_id="t1",
        parent_span_id=root.span_id,
        name="anthropic.call",
        start_time=now + timedelta(milliseconds=1),
    )

    summary = TraceSummary.from_spans("t1", [root, child])

    assert summary.root_span_name == "gateway.chat"
    assert summary.span_count == 2


def test_from_spans_falls_back_to_earliest_span_when_no_root_present():
    now = datetime.now(UTC)
    earlier = make_span(trace_id="t1", parent_span_id="some-parent", start_time=now)
    later = make_span(trace_id="t1", parent_span_id="some-parent", start_time=now + timedelta(seconds=1))

    summary = TraceSummary.from_spans("t1", [later, earlier])

    assert summary.root_span_name == earlier.name


def test_from_spans_reports_error_if_any_span_errored():
    now = datetime.now(UTC)
    ok_span = make_span(trace_id="t1", status=SpanStatus.OK, start_time=now)
    error_span = make_span(trace_id="t1", status=SpanStatus.ERROR, start_time=now)

    summary = TraceSummary.from_spans("t1", [ok_span, error_span])

    assert summary.status == SpanStatus.ERROR
