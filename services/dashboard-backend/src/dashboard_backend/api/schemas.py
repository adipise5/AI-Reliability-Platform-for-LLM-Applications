from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from dashboard_backend.domain.entities import (
    DashboardOverview,
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
    RunDetail,
)


class RemoteEvalRunOut(BaseModel):
    id: UUID
    prompt_id: UUID
    prompt_version_id: UUID
    dataset_id: UUID
    dataset_version: int | None
    model: str
    status: str
    aggregate_score: float | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, run: RemoteEvalRun) -> RemoteEvalRunOut:
        return cls(
            id=run.id,
            prompt_id=run.prompt_id,
            prompt_version_id=run.prompt_version_id,
            dataset_id=run.dataset_id,
            dataset_version=run.dataset_version,
            model=run.model,
            status=run.status,
            aggregate_score=run.aggregate_score,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )


class RemoteScoreOut(BaseModel):
    scorer_name: str
    value: float

    @classmethod
    def from_domain(cls, score: RemoteScore) -> RemoteScoreOut:
        return cls(scorer_name=score.scorer_name, value=score.value)


class RemoteRunItemResultOut(BaseModel):
    id: UUID
    dataset_item_id: UUID
    output: str
    latency_ms: float
    scores: list[RemoteScoreOut]

    @classmethod
    def from_domain(cls, item: RemoteRunItemResult) -> RemoteRunItemResultOut:
        return cls(
            id=item.id,
            dataset_item_id=item.dataset_item_id,
            output=item.output,
            latency_ms=item.latency_ms,
            scores=[RemoteScoreOut.from_domain(s) for s in item.scores],
        )


class RemoteGateDecisionOut(BaseModel):
    run_id: UUID
    verdict: str
    observed_score: float
    baseline_mean: float
    baseline_stddev: float

    @classmethod
    def from_domain(cls, decision: RemoteGateDecision) -> RemoteGateDecisionOut:
        return cls(
            run_id=decision.run_id,
            verdict=decision.verdict,
            observed_score=decision.observed_score,
            baseline_mean=decision.baseline_mean,
            baseline_stddev=decision.baseline_stddev,
        )


class RunDetailOut(BaseModel):
    run: RemoteEvalRunOut
    items: list[RemoteRunItemResultOut]
    gate_decision: RemoteGateDecisionOut | None

    @classmethod
    def from_domain(cls, detail: RunDetail) -> RunDetailOut:
        return cls(
            run=RemoteEvalRunOut.from_domain(detail.run),
            items=[RemoteRunItemResultOut.from_domain(i) for i in detail.items],
            gate_decision=(
                RemoteGateDecisionOut.from_domain(detail.gate_decision)
                if detail.gate_decision is not None
                else None
            ),
        )


class RemoteModelUsageOut(BaseModel):
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float

    @classmethod
    def from_domain(cls, usage: RemoteModelUsage) -> RemoteModelUsageOut:
        return cls(
            provider=usage.provider,
            model=usage.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cost_usd=usage.cost_usd,
        )


class RemoteUsageSummaryOut(BaseModel):
    total_cost_usd: float
    total_prompt_tokens: int
    total_completion_tokens: int
    by_model: list[RemoteModelUsageOut]

    @classmethod
    def from_domain(cls, summary: RemoteUsageSummary) -> RemoteUsageSummaryOut:
        return cls(
            total_cost_usd=summary.total_cost_usd,
            total_prompt_tokens=summary.total_prompt_tokens,
            total_completion_tokens=summary.total_completion_tokens,
            by_model=[RemoteModelUsageOut.from_domain(m) for m in summary.by_model],
        )


class RemoteBudgetStatusOut(BaseModel):
    spent_this_month_usd: float
    limit_usd: float | None
    remaining_usd: float | None
    over_budget: bool

    @classmethod
    def from_domain(cls, status: RemoteBudgetStatus) -> RemoteBudgetStatusOut:
        return cls(
            spent_this_month_usd=status.spent_this_month_usd,
            limit_usd=status.limit_usd,
            remaining_usd=status.remaining_usd,
            over_budget=status.over_budget,
        )


class RemoteBaselineOut(BaseModel):
    prompt_id: UUID
    mean_score: float
    stddev_score: float
    sample_size: int

    @classmethod
    def from_domain(cls, baseline: RemoteBaseline) -> RemoteBaselineOut:
        return cls(
            prompt_id=baseline.prompt_id,
            mean_score=baseline.mean_score,
            stddev_score=baseline.stddev_score,
            sample_size=baseline.sample_size,
        )


class RemoteLatencyAnomalyOut(BaseModel):
    sample_count: int
    recent_mean_ms: float | None
    baseline_mean_ms: float | None
    baseline_stddev_ms: float | None
    is_anomalous: bool
    insufficient_data: bool

    @classmethod
    def from_domain(cls, anomaly: RemoteLatencyAnomaly) -> RemoteLatencyAnomalyOut:
        return cls(
            sample_count=anomaly.sample_count,
            recent_mean_ms=anomaly.recent_mean_ms,
            baseline_mean_ms=anomaly.baseline_mean_ms,
            baseline_stddev_ms=anomaly.baseline_stddev_ms,
            is_anomalous=anomaly.is_anomalous,
            insufficient_data=anomaly.insufficient_data,
        )


class RemoteReportOut(BaseModel):
    id: UUID
    experiment_id: UUID
    format: str
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, report: RemoteReport) -> RemoteReportOut:
        return cls(
            id=report.id,
            experiment_id=report.experiment_id,
            format=report.format,
            status=report.status,
            error_message=report.error_message,
            created_at=report.created_at,
            completed_at=report.completed_at,
        )


class RemoteChannelOut(BaseModel):
    id: UUID
    channel_type: str
    name: str
    target: str
    enabled: bool

    @classmethod
    def from_domain(cls, channel: RemoteChannel) -> RemoteChannelOut:
        return cls(
            id=channel.id,
            channel_type=channel.channel_type,
            name=channel.name,
            target=channel.target,
            enabled=channel.enabled,
        )


class RemoteNotificationOut(BaseModel):
    id: UUID
    channel_id: UUID
    subject: str
    status: str
    created_at: datetime

    @classmethod
    def from_domain(cls, notification: RemoteNotification) -> RemoteNotificationOut:
        return cls(
            id=notification.id,
            channel_id=notification.channel_id,
            subject=notification.subject,
            status=notification.status,
            created_at=notification.created_at,
        )


class RemoteCheckRunOut(BaseModel):
    id: UUID
    repo: str
    commit_sha: str
    status: str
    conclusion: str | None
    run_id: UUID | None

    @classmethod
    def from_domain(cls, check: RemoteCheckRun) -> RemoteCheckRunOut:
        return cls(
            id=check.id,
            repo=check.repo,
            commit_sha=check.commit_sha,
            status=check.status,
            conclusion=check.conclusion,
            run_id=check.run_id,
        )


class RemoteTraceSummaryOut(BaseModel):
    trace_id: str
    root_span_name: str
    span_count: int
    status: str
    duration_ms: float

    @classmethod
    def from_domain(cls, trace: RemoteTraceSummary) -> RemoteTraceSummaryOut:
        return cls(
            trace_id=trace.trace_id,
            root_span_name=trace.root_span_name,
            span_count=trace.span_count,
            status=trace.status,
            duration_ms=trace.duration_ms,
        )


class DashboardOverviewOut(BaseModel):
    recent_runs: list[RemoteEvalRunOut]
    cost_summary: RemoteUsageSummaryOut | None
    budget_status: RemoteBudgetStatusOut | None
    latency_anomaly: RemoteLatencyAnomalyOut | None
    recent_notifications: list[RemoteNotificationOut]

    @classmethod
    def from_domain(cls, overview: DashboardOverview) -> DashboardOverviewOut:
        return cls(
            recent_runs=[RemoteEvalRunOut.from_domain(r) for r in overview.recent_runs],
            cost_summary=(
                RemoteUsageSummaryOut.from_domain(overview.cost_summary)
                if overview.cost_summary is not None
                else None
            ),
            budget_status=(
                RemoteBudgetStatusOut.from_domain(overview.budget_status)
                if overview.budget_status is not None
                else None
            ),
            latency_anomaly=(
                RemoteLatencyAnomalyOut.from_domain(overview.latency_anomaly)
                if overview.latency_anomaly is not None
                else None
            ),
            recent_notifications=[
                RemoteNotificationOut.from_domain(n) for n in overview.recent_notifications
            ],
        )


class ErrorOut(BaseModel):
    type: str
    message: str
