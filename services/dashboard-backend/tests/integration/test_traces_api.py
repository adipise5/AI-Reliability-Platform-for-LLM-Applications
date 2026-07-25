from __future__ import annotations

from tests.unit.conftest import make_trace


def test_list_traces_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get("/api/v1/traces")

    assert response.status_code == 401


def test_list_traces_returns_traces(client, trace_reader):
    trace = make_trace()
    trace_reader.traces = [trace]

    response = client.get("/api/v1/traces")

    assert response.status_code == 200
    assert [t["trace_id"] for t in response.json()] == [trace.trace_id]
