from __future__ import annotations

import json

import httpx
import respx
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode

from gateway.infrastructure.observability.trace_collector_exporter import TraceCollectorSpanExporter

BASE_URL = "http://trace-collector.internal"


def _make_finished_span(*, status_code: StatusCode = StatusCode.OK):
    capture = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(capture))
    tracer = provider.get_tracer("test")

    span = tracer.start_span("gateway.chat")
    span.set_attribute("model", "claude-sonnet-5")
    span.set_status(Status(status_code))
    span.end()

    (finished,) = capture.get_finished_spans()
    return finished


@respx.mock
def test_export_posts_the_span_batch_and_returns_success():
    route = respx.post(f"{BASE_URL}/api/v1/traces").mock(return_value=httpx.Response(202))
    exporter = TraceCollectorSpanExporter(BASE_URL)
    span = _make_finished_span()

    result = exporter.export([span])

    assert result == SpanExportResult.SUCCESS
    body = json.loads(route.calls.last.request.content)
    (wire_span,) = body["spans"]
    assert wire_span["name"] == "gateway.chat"
    assert wire_span["status"] == "OK"
    assert wire_span["attributes"] == {"model": "claude-sonnet-5"}
    assert len(wire_span["trace_id"]) == 32
    assert len(wire_span["span_id"]) == 16
    assert wire_span["parent_span_id"] is None


@respx.mock
def test_export_reports_error_status():
    respx.post(f"{BASE_URL}/api/v1/traces").mock(return_value=httpx.Response(202))
    exporter = TraceCollectorSpanExporter(BASE_URL)
    span = _make_finished_span(status_code=StatusCode.ERROR)

    exporter.export([span])

    request = respx.calls.last.request
    body = json.loads(request.content)
    assert body["spans"][0]["status"] == "ERROR"


@respx.mock
def test_export_returns_failure_instead_of_raising_on_5xx():
    respx.post(f"{BASE_URL}/api/v1/traces").mock(return_value=httpx.Response(503))
    exporter = TraceCollectorSpanExporter(BASE_URL)
    span = _make_finished_span()

    result = exporter.export([span])

    assert result == SpanExportResult.FAILURE


@respx.mock
def test_export_returns_failure_instead_of_raising_on_connection_error():
    respx.post(f"{BASE_URL}/api/v1/traces").mock(side_effect=httpx.ConnectError("refused"))
    exporter = TraceCollectorSpanExporter(BASE_URL)
    span = _make_finished_span()

    result = exporter.export([span])

    assert result == SpanExportResult.FAILURE
