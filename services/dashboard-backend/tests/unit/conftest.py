from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from dashboard_backend.domain.entities import (
    RemoteBaseline,
    RemoteBudgetStatus,
    RemoteChannel,
    RemoteCheckRun,
    RemoteEvalRun,
    RemoteGateDecision,
    RemoteLatencyAnomaly,
    RemoteModelUsage,
    RemoteNotification,
    RemoteReport,
    RemoteRunItemResult,
    RemoteScore,
    RemoteTraceSummary,
    RemoteUsageSummary,
)
from dashboard_backend.domain.errors import ReportNotFoundError, RunNotFoundError


class FakeEvalRunReader:
    def __init__(
        self,
        runs: list[RemoteEvalRun] | None = None,
        items_by_run: dict[UUID, tuple[RemoteRunItemResult, ...]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.runs = {r.id: r for r in (runs or [])}
        self.items_by_run = items_by_run or {}
        self.error = error

    async def list_runs(self, credential: str) -> list[RemoteEvalRun]:
        if self.error is not None:
            raise self.error
        return list(self.runs.values())

    async def get_run(
        self, credential: str, run_id: UUID
    ) -> tuple[RemoteEvalRun, tuple[RemoteRunItemResult, ...]]:
        if run_id not in self.runs:
            raise RunNotFoundError(run_id)
        return self.runs[run_id], self.items_by_run.get(run_id, ())


class FakeCostReader:
    def __init__(
        self,
        summary: RemoteUsageSummary | None = None,
        budget: RemoteBudgetStatus | None = None,
        error: Exception | None = None,
    ) -> None:
        self.summary = summary or make_usage_summary()
        self.budget = budget or make_budget_status()
        self.error = error

    async def get_usage_summary(self, credential: str) -> RemoteUsageSummary:
        if self.error is not None:
            raise self.error
        return self.summary

    async def get_budget_status(self, credential: str) -> RemoteBudgetStatus:
        if self.error is not None:
            raise self.error
        return self.budget


class FakeRegressionReader:
    def __init__(
        self,
        baselines: dict[UUID, RemoteBaseline] | None = None,
        gate_decisions: dict[UUID, RemoteGateDecision] | None = None,
        latency_anomaly: RemoteLatencyAnomaly | None = None,
        error: Exception | None = None,
    ) -> None:
        self.baselines = baselines or {}
        self.gate_decisions = gate_decisions or {}
        self.latency_anomaly = latency_anomaly or make_latency_anomaly()
        self.error = error

    async def get_baseline(self, credential: str, prompt_id: UUID) -> RemoteBaseline | None:
        return self.baselines.get(prompt_id)

    async def get_gate_decision(self, credential: str, run_id: UUID) -> RemoteGateDecision | None:
        return self.gate_decisions.get(run_id)

    async def get_latency_anomaly(self) -> RemoteLatencyAnomaly:
        if self.error is not None:
            raise self.error
        return self.latency_anomaly


class FakeReportReader:
    def __init__(self, reports: list[RemoteReport] | None = None) -> None:
        self.reports = {r.id: r for r in (reports or [])}

    async def list_reports(
        self, credential: str, *, experiment_id: UUID | None = None
    ) -> list[RemoteReport]:
        matches = list(self.reports.values())
        if experiment_id is not None:
            matches = [r for r in matches if r.experiment_id == experiment_id]
        return matches

    async def get_report(self, credential: str, report_id: UUID) -> RemoteReport:
        if report_id not in self.reports:
            raise ReportNotFoundError(report_id)
        return self.reports[report_id]


class FakeNotificationReader:
    def __init__(
        self,
        channels: list[RemoteChannel] | None = None,
        notifications: list[RemoteNotification] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.channels = channels or []
        self.notifications = notifications or []
        self.error = error

    async def list_channels(self, credential: str) -> list[RemoteChannel]:
        return self.channels

    async def list_notifications(
        self, credential: str, *, channel_id: UUID | None = None
    ) -> list[RemoteNotification]:
        if self.error is not None:
            raise self.error
        matches = self.notifications
        if channel_id is not None:
            matches = [n for n in matches if n.channel_id == channel_id]
        return matches


class FakeGitHubChecksReader:
    def __init__(self, checks: list[RemoteCheckRun] | None = None) -> None:
        self.checks = checks or []

    async def list_checks(
        self, credential: str, *, repo: str | None = None, commit_sha: str | None = None
    ) -> list[RemoteCheckRun]:
        matches = self.checks
        if repo is not None:
            matches = [c for c in matches if c.repo == repo]
        if commit_sha is not None:
            matches = [c for c in matches if c.commit_sha == commit_sha]
        return matches


class FakeTraceReader:
    def __init__(self, traces: list[RemoteTraceSummary] | None = None) -> None:
        self.traces = traces or []

    async def list_recent_traces(self, limit: int) -> list[RemoteTraceSummary]:
        return self.traces[:limit]


def make_run(**overrides: object) -> RemoteEvalRun:
    base = RemoteEvalRun(
        id=uuid4(),
        prompt_id=uuid4(),
        prompt_version_id=uuid4(),
        dataset_id=uuid4(),
        dataset_version=1,
        model="claude-sonnet-5",
        status="completed",
        aggregate_score=0.9,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    return replace(base, **overrides)


def make_run_item(**overrides: object) -> RemoteRunItemResult:
    base = RemoteRunItemResult(
        id=uuid4(),
        dataset_item_id=uuid4(),
        output="the output",
        latency_ms=120.0,
        scores=(RemoteScore(scorer_name="exact_match", value=1.0),),
    )
    return replace(base, **overrides)


def make_gate_decision(**overrides: object) -> RemoteGateDecision:
    base = RemoteGateDecision(
        run_id=uuid4(), verdict="pass", observed_score=0.9, baseline_mean=0.85, baseline_stddev=0.05
    )
    return replace(base, **overrides)


def make_usage_summary(**overrides: object) -> RemoteUsageSummary:
    base = RemoteUsageSummary(
        total_cost_usd=1.23,
        total_prompt_tokens=1000,
        total_completion_tokens=500,
        by_model=(
            RemoteModelUsage(
                provider="anthropic",
                model="claude-sonnet-5",
                prompt_tokens=1000,
                completion_tokens=500,
                cost_usd=1.23,
            ),
        ),
    )
    return replace(base, **overrides)


def make_budget_status(**overrides: object) -> RemoteBudgetStatus:
    base = RemoteBudgetStatus(
        spent_this_month_usd=1.23, limit_usd=100.0, remaining_usd=98.77, over_budget=False
    )
    return replace(base, **overrides)


def make_baseline(**overrides: object) -> RemoteBaseline:
    base = RemoteBaseline(prompt_id=uuid4(), mean_score=0.9, stddev_score=0.05, sample_size=5)
    return replace(base, **overrides)


def make_latency_anomaly(**overrides: object) -> RemoteLatencyAnomaly:
    base = RemoteLatencyAnomaly(
        sample_count=20,
        recent_mean_ms=120.0,
        baseline_mean_ms=100.0,
        baseline_stddev_ms=10.0,
        is_anomalous=False,
        insufficient_data=False,
    )
    return replace(base, **overrides)


def make_report(**overrides: object) -> RemoteReport:
    base = RemoteReport(
        id=uuid4(),
        experiment_id=uuid4(),
        format="html",
        status="ready",
        error_message=None,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    return replace(base, **overrides)


def make_channel(**overrides: object) -> RemoteChannel:
    base = RemoteChannel(
        id=uuid4(), channel_type="slack", name="alerts", target="https://hooks.slack.example/x", enabled=True
    )
    return replace(base, **overrides)


def make_notification(**overrides: object) -> RemoteNotification:
    base = RemoteNotification(
        id=uuid4(), channel_id=uuid4(), subject="s", status="sent", created_at=datetime.now(UTC)
    )
    return replace(base, **overrides)


def make_check(**overrides: object) -> RemoteCheckRun:
    base = RemoteCheckRun(
        id=uuid4(),
        repo="acme/widgets",
        commit_sha="a" * 40,
        status="completed",
        conclusion="success",
        run_id=uuid4(),
    )
    return replace(base, **overrides)


def make_trace(**overrides: object) -> RemoteTraceSummary:
    base = RemoteTraceSummary(
        trace_id=uuid4().hex, root_span_name="gateway.chat", span_count=3, status="OK", duration_ms=120.0
    )
    return replace(base, **overrides)
