"""Use case: is the Gateway getting slower right now, compared to its own
recent history? A stateless computation over Trace Collector trace
summaries — nothing here is persisted, since it's always answerable fresh
from source and there's no consumer yet (a future Dashboard) that needs a
stored history of past checks.

Splits the most recent `list_recent_traces` results into two windows: the
last `recent_count` traces ("right now") versus everything older up to
`limit` ("recent history"), and flags an anomaly if the recent window's
mean duration is more than `stddev_threshold` standard deviations above
the baseline window's mean.
"""

from __future__ import annotations

import statistics

from regression_detection.domain.entities import LatencyAnomalyCheck
from regression_detection.domain.ports import TraceReader


class CheckLatencyAnomalyUseCase:
    def __init__(
        self,
        trace_reader: TraceReader,
        *,
        stddev_threshold: float = 2.0,
        recent_count: int = 5,
        minimum_baseline_size: int = 5,
    ) -> None:
        self._trace_reader = trace_reader
        self._stddev_threshold = stddev_threshold
        self._recent_count = recent_count
        self._minimum_baseline_size = minimum_baseline_size

    async def execute(self, *, limit: int = 50) -> LatencyAnomalyCheck:
        traces = await self._trace_reader.list_recent_traces(limit)

        recent = traces[: self._recent_count]
        baseline_pool = traces[self._recent_count :]

        if len(recent) < self._recent_count or len(baseline_pool) < self._minimum_baseline_size:
            return LatencyAnomalyCheck(
                sample_count=len(traces),
                recent_mean_ms=None,
                baseline_mean_ms=None,
                baseline_stddev_ms=None,
                is_anomalous=False,
                insufficient_data=True,
            )

        baseline_durations = [t.duration_ms for t in baseline_pool]
        recent_durations = [t.duration_ms for t in recent]
        baseline_mean = statistics.fmean(baseline_durations)
        baseline_stddev = statistics.pstdev(baseline_durations)
        recent_mean = statistics.fmean(recent_durations)

        if baseline_stddev == 0:
            is_anomalous = recent_mean > baseline_mean
        else:
            is_anomalous = (recent_mean - baseline_mean) / baseline_stddev >= self._stddev_threshold

        return LatencyAnomalyCheck(
            sample_count=len(traces),
            recent_mean_ms=recent_mean,
            baseline_mean_ms=baseline_mean,
            baseline_stddev_ms=baseline_stddev,
            is_anomalous=is_anomalous,
            insufficient_data=False,
        )
