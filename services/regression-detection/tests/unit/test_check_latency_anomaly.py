from __future__ import annotations

from regression_detection.application.check_latency_anomaly import CheckLatencyAnomalyUseCase
from tests.unit.conftest import FakeTraceReader, make_trace


async def test_insufficient_data_when_too_few_traces():
    reader = FakeTraceReader([make_trace() for _ in range(3)])
    use_case = CheckLatencyAnomalyUseCase(reader)

    result = await use_case.execute(limit=50)

    assert result.insufficient_data is True
    assert result.is_anomalous is False
    assert result.recent_mean_ms is None


async def test_not_anomalous_when_recent_matches_history():
    traces = [make_trace(duration_ms=100.0) for _ in range(15)]
    reader = FakeTraceReader(traces)
    use_case = CheckLatencyAnomalyUseCase(reader)

    result = await use_case.execute(limit=50)

    assert result.insufficient_data is False
    assert result.is_anomalous is False


async def test_anomalous_when_recent_window_is_much_slower():
    recent = [make_trace(duration_ms=500.0) for _ in range(5)]
    baseline = [make_trace(duration_ms=100.0) for _ in range(10)]
    reader = FakeTraceReader([*recent, *baseline])
    use_case = CheckLatencyAnomalyUseCase(reader)

    result = await use_case.execute(limit=50)

    assert result.insufficient_data is False
    assert result.is_anomalous is True
    assert result.recent_mean_ms == 500.0
    assert result.baseline_mean_ms == 100.0


async def test_not_anomalous_when_recent_window_is_within_stddev_threshold():
    recent = [make_trace(duration_ms=110.0) for _ in range(5)]
    baseline = [
        make_trace(duration_ms=90.0),
        make_trace(duration_ms=110.0),
        make_trace(duration_ms=90.0),
        make_trace(duration_ms=110.0),
        make_trace(duration_ms=100.0),
        make_trace(duration_ms=100.0),
    ]
    reader = FakeTraceReader([*recent, *baseline])
    use_case = CheckLatencyAnomalyUseCase(reader)

    result = await use_case.execute(limit=50)

    assert result.is_anomalous is False
