"""Domain entities for the Trace Collector — see ADR-0001: no framework
imports here.

This is intentionally OTel-*shaped*, not OTLP-*compliant*: spans carry the
same concepts (trace/span id, parent, name, status, timing, flat
attributes) the OpenTelemetry SDK produces, but ingestion speaks a small
custom JSON shape rather than the OTLP protobuf wire format. A full OTLP
receiver is a straightforward later swap of the ingestion adapter — it
doesn't change this domain model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

AttributeValue = str | int | float | bool


class SpanStatus(StrEnum):
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class Span:
    id: str
    """The row's own identity — a UUID, unrelated to OTel's trace/span ids."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    status: SpanStatus
    start_time: datetime
    end_time: datetime
    attributes: dict[str, AttributeValue] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time).total_seconds() * 1000


@dataclass(frozen=True, slots=True)
class TraceSummary:
    trace_id: str
    root_span_name: str
    span_count: int
    status: SpanStatus
    started_at: datetime
    duration_ms: float

    @classmethod
    def from_spans(cls, trace_id: str, spans: list[Span]) -> TraceSummary:
        root = next((s for s in spans if s.parent_span_id is None), min(spans, key=lambda s: s.start_time))
        started_at = min(s.start_time for s in spans)
        ended_at = max(s.end_time for s in spans)
        status = SpanStatus.ERROR if any(s.status == SpanStatus.ERROR for s in spans) else SpanStatus.OK
        return cls(
            trace_id=trace_id,
            root_span_name=root.name,
            span_count=len(spans),
            status=status,
            started_at=started_at,
            duration_ms=(ended_at - started_at).total_seconds() * 1000,
        )
