"""The real `TracingSink` adapter, backed by the OpenTelemetry SDK.

`TracingSink.emit_span` reports a span *after* the operation has already
finished (`RouteChatUseCase`/`StreamChatUseCase` call it from a `finally`
block with a precomputed `duration_ms`) — it doesn't wrap the call in a
`with tracer.start_as_current_span(...):` block the way most OTel
instrumentation does. Reworking the use cases to carry a live span through
their `execute()` calls would ripple into Week 1/2 code and tests for no
behavioral gain, so instead this adapter reconstructs an equivalent span
after the fact: it opens a span with an explicit `start_time` computed
from the duration, sets attributes and status, and immediately ends it
with an explicit `end_time`. The resulting span is indistinguishable from
one produced by the context-manager style, once it reaches the exporter.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from opentelemetry.trace import Status, StatusCode, Tracer


class OtelTracingSink:
    def __init__(self, tracer: Tracer) -> None:
        self._tracer = tracer

    async def emit_span(
        self,
        *,
        name: str,
        status: str,
        duration_ms: float,
        attributes: dict[str, str | int | float | bool],
    ) -> None:
        end = datetime.now(UTC)
        start = end - timedelta(milliseconds=duration_ms)
        span = self._tracer.start_span(name, start_time=_to_nanoseconds(start))
        try:
            for key, value in attributes.items():
                span.set_attribute(key, value)
            span.set_status(Status(StatusCode.ERROR if status == "error" else StatusCode.OK))
        finally:
            span.end(end_time=_to_nanoseconds(end))


def _to_nanoseconds(moment: datetime) -> int:
    return int(moment.timestamp() * 1_000_000_000)
