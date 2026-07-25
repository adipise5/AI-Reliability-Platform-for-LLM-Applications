"""A `SpanExporter` that ships finished spans to the Trace Collector's
ingestion endpoint (see services/trace-collector), rather than to a full
OTel Collector — see that service's README for why the wire format is a
small custom JSON shape rather than OTLP.

`SpanExporter.export()` is synchronous by contract: the SDK's
`BatchSpanProcessor` calls it from its own background worker thread, so
this uses a plain `httpx.Client`, not the async client used everywhere
else in the gateway. Exporters must never raise — any failure here
becomes a dropped batch of spans, not a broken chat request.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import httpx
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import StatusCode

_STATUS_NAMES = {
    StatusCode.OK: "OK",
    StatusCode.ERROR: "ERROR",
    StatusCode.UNSET: "UNSET",
}


class TraceCollectorSpanExporter(SpanExporter):
    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            response = self._client.post(
                "/api/v1/traces", json={"spans": [_to_wire(span) for span in spans]}
            )
            response.raise_for_status()
        except Exception:  # exporter contract: never raise, report FAILURE instead
            return SpanExportResult.FAILURE
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        self._client.close()


def _to_wire(span: ReadableSpan) -> dict[str, object]:
    context = span.get_span_context()
    assert context is not None, "a finished span always has a context"
    parent_span_id = format(span.parent.span_id, "016x") if span.parent else None
    return {
        "trace_id": format(context.trace_id, "032x"),
        "span_id": format(context.span_id, "016x"),
        "parent_span_id": parent_span_id,
        "name": span.name,
        "status": _STATUS_NAMES[span.status.status_code],
        "start_time": _ns_to_iso(span.start_time),
        "end_time": _ns_to_iso(span.end_time),
        "attributes": dict(span.attributes or {}),
    }


def _ns_to_iso(nanoseconds: int | None) -> str:
    assert nanoseconds is not None
    return datetime.fromtimestamp(nanoseconds / 1e9, tz=UTC).isoformat()
