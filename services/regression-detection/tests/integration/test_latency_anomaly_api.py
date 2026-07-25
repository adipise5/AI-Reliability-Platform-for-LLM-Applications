from __future__ import annotations

from tests.unit.conftest import make_trace


def test_latency_anomaly_requires_no_authentication(client):
    response = client.get("/api/v1/latency-anomaly")

    assert response.status_code == 200


def test_latency_anomaly_reports_insufficient_data_with_no_traces(client):
    response = client.get("/api/v1/latency-anomaly")

    body = response.json()
    assert body["insufficient_data"] is True
    assert body["is_anomalous"] is False


def test_latency_anomaly_flags_a_slow_recent_window(client, trace_reader):
    trace_reader.traces = [make_trace(duration_ms=500.0) for _ in range(5)] + [
        make_trace(duration_ms=100.0) for _ in range(10)
    ]

    response = client.get("/api/v1/latency-anomaly")

    body = response.json()
    assert body["insufficient_data"] is False
    assert body["is_anomalous"] is True
