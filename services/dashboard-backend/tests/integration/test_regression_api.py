from __future__ import annotations

from uuid import uuid4

from tests.unit.conftest import make_baseline


def test_get_baseline_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get(f"/api/v1/regression/baselines/{uuid4()}")

    assert response.status_code == 401


def test_get_baseline_returns_null_when_never_gated(client):
    response = client.get(f"/api/v1/regression/baselines/{uuid4()}")

    assert response.status_code == 200
    assert response.json() is None


def test_get_baseline_returns_the_baseline(client, regression_reader):
    prompt_id = uuid4()
    baseline = make_baseline(prompt_id=prompt_id)
    regression_reader.baselines[prompt_id] = baseline

    response = client.get(f"/api/v1/regression/baselines/{prompt_id}")

    assert response.status_code == 200
    assert response.json()["sample_size"] == baseline.sample_size


def test_get_latency_anomaly_returns_the_check(client):
    response = client.get("/api/v1/regression/latency-anomaly")

    assert response.status_code == 200
    assert "is_anomalous" in response.json()
