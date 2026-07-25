from __future__ import annotations

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from gateway.infrastructure.observability.otel_tracing_sink import OtelTracingSink


def _build_sink() -> tuple[OtelTracingSink, InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")
    return OtelTracingSink(tracer), exporter


async def test_emit_span_produces_a_finished_span_with_attributes_and_ok_status():
    sink, exporter = _build_sink()

    await sink.emit_span(
        name="gateway.chat", status="ok", duration_ms=12.5, attributes={"model": "claude-sonnet-5"}
    )

    (span,) = exporter.get_finished_spans()
    assert span.name == "gateway.chat"
    assert span.status.status_code == StatusCode.OK
    assert span.attributes["model"] == "claude-sonnet-5"


async def test_emit_span_marks_error_status():
    sink, exporter = _build_sink()

    await sink.emit_span(name="gateway.chat", status="error", duration_ms=1.0, attributes={})

    (span,) = exporter.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR


async def test_emit_span_reconstructs_the_original_duration():
    sink, exporter = _build_sink()

    await sink.emit_span(name="gateway.chat", status="ok", duration_ms=250.0, attributes={})

    (span,) = exporter.get_finished_spans()
    assert span.start_time is not None
    assert span.end_time is not None
    observed_ms = (span.end_time - span.start_time) / 1_000_000
    # float64 can't represent nanoseconds-since-epoch exactly at this
    # magnitude, so the round trip through datetime.timestamp() loses a
    # handful of microseconds — assert "close enough," not bit-exact.
    assert observed_ms == pytest.approx(250.0, abs=0.01)
