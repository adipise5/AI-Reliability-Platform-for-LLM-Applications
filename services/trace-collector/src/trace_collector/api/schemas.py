from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from trace_collector.domain.entities import AttributeValue, Span, SpanStatus, TraceSummary


class SpanIn(BaseModel):
    trace_id: str = Field(..., min_length=1, max_length=32)
    span_id: str = Field(..., min_length=1, max_length=16)
    parent_span_id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    status: Literal["UNSET", "OK", "ERROR"] = "UNSET"
    start_time: datetime
    end_time: datetime
    attributes: dict[str, AttributeValue] = Field(default_factory=dict)

    def to_domain(self) -> Span:
        return Span(
            id=str(uuid4()),
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=self.parent_span_id,
            name=self.name,
            status=SpanStatus(self.status),
            start_time=self.start_time,
            end_time=self.end_time,
            attributes=self.attributes,
        )


class IngestSpansIn(BaseModel):
    spans: list[SpanIn] = Field(..., min_length=1)


class IngestSpansOut(BaseModel):
    ingested: int


class SpanOut(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    attributes: dict[str, AttributeValue]

    @classmethod
    def from_domain(cls, span: Span) -> SpanOut:
        return cls(
            trace_id=span.trace_id,
            span_id=span.span_id,
            parent_span_id=span.parent_span_id,
            name=span.name,
            status=span.status.value,
            start_time=span.start_time,
            end_time=span.end_time,
            duration_ms=span.duration_ms,
            attributes=span.attributes,
        )


class TraceOut(BaseModel):
    trace_id: str
    spans: list[SpanOut]


class TraceSummaryOut(BaseModel):
    trace_id: str
    root_span_name: str
    span_count: int
    status: str
    started_at: datetime
    duration_ms: float

    @classmethod
    def from_domain(cls, summary: TraceSummary) -> TraceSummaryOut:
        return cls(
            trace_id=summary.trace_id,
            root_span_name=summary.root_span_name,
            span_count=summary.span_count,
            status=summary.status.value,
            started_at=summary.started_at,
            duration_ms=summary.duration_ms,
        )


class ErrorOut(BaseModel):
    type: str
    message: str
