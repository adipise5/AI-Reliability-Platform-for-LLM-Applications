from __future__ import annotations

from dashboard_backend.application.get_latency_anomaly import GetLatencyAnomalyUseCase
from tests.unit.conftest import FakeRegressionReader, make_latency_anomaly


async def test_returns_the_latency_anomaly_check():
    anomaly = make_latency_anomaly(is_anomalous=True)
    use_case = GetLatencyAnomalyUseCase(FakeRegressionReader(latency_anomaly=anomaly))

    result = await use_case.execute()

    assert result == anomaly
