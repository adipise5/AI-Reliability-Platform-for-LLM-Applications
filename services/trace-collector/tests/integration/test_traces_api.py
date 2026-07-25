from __future__ import annotations

from datetime import UTC, datetime, timedelta


def _span_payload(trace_id: str, *, status: str = "OK", start: datetime | None = None) -> dict:
    start_time = start or datetime.now(UTC)
    end_time = start_time + timedelta(milliseconds=15)
    return {
        "trace_id": trace_id,
        "span_id": "span1",
        "parent_span_id": None,
        "name": "gateway.chat",
        "status": status,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "attributes": {"model": "claude-sonnet-5", "stream": False},
    }


def test_ingest_rejects_an_empty_batch(client):
    response = client.post("/api/v1/traces", json={"spans": []})

    assert response.status_code == 422  # min_length=1 on the request schema


def test_ingest_then_get_trace_round_trip(client):
    payload = {"spans": [_span_payload("trace-a")]}

    ingested = client.post("/api/v1/traces", json=payload)
    assert ingested.status_code == 202
    assert ingested.json() == {"ingested": 1}

    fetched = client.get("/api/v1/traces/trace-a")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["trace_id"] == "trace-a"
    assert len(body["spans"]) == 1
    assert body["spans"][0]["attributes"]["model"] == "claude-sonnet-5"


def test_get_unknown_trace_returns_404(client):
    response = client.get("/api/v1/traces/does-not-exist")

    assert response.status_code == 404
    assert response.json()["type"] == "trace_not_found"


def test_list_traces_orders_most_recent_first(client):
    now = datetime.now(UTC)
    client.post("/api/v1/traces", json={"spans": [_span_payload("older", start=now - timedelta(hours=1))]})
    client.post("/api/v1/traces", json={"spans": [_span_payload("newer", start=now)]})

    response = client.get("/api/v1/traces")

    assert response.status_code == 200
    trace_ids = [t["trace_id"] for t in response.json()]
    assert trace_ids == ["newer", "older"]


def test_list_traces_reports_error_status_rollup(client):
    client.post("/api/v1/traces", json={"spans": [_span_payload("erroring", status="ERROR")]})

    response = client.get("/api/v1/traces")

    assert response.json()[0]["status"] == "ERROR"
