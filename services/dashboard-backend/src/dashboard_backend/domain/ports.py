"""Ports: interfaces the application layer depends on — one per
upstream service this BFF fans out to. Every one is an HTTP client to
another bounded context; there's no repository port at all, since this
service persists nothing.

A recurring design choice across these ports: a 404 for a query that's
naturally "is there data yet for X" (a baseline, a gate decision) comes
back as `None`, not an exception — absence is an expected, ordinary
state for a prompt that's never been gated, not a failure. A 404 for a
lookup by a caller-supplied id that's supposed to identify something
real (a specific run, a specific report) still raises a `*NotFoundError`,
since that really is "you asked for something that doesn't exist."
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from dashboard_backend.domain.entities import (
    RemoteBaseline,
    RemoteBudgetStatus,
    RemoteChannel,
    RemoteCheckRun,
    RemoteEvalRun,
    RemoteGateDecision,
    RemoteLatencyAnomaly,
    RemoteNotification,
    RemoteReport,
    RemoteRunItemResult,
    RemoteTraceSummary,
    RemoteUsageSummary,
)


class EvalRunReader(Protocol):
    async def list_runs(self, credential: str) -> list[RemoteEvalRun]: ...

    async def get_run(
        self, credential: str, run_id: UUID
    ) -> tuple[RemoteEvalRun, tuple[RemoteRunItemResult, ...]]:
        """Raises `dashboard_backend.domain.errors.RunNotFoundError` on a
        404 — a run id came from the caller, so absence is a real
        error."""
        ...


class CostReader(Protocol):
    async def get_usage_summary(self, credential: str) -> RemoteUsageSummary: ...

    async def get_budget_status(self, credential: str) -> RemoteBudgetStatus: ...


class RegressionReader(Protocol):
    async def get_baseline(self, credential: str, prompt_id: UUID) -> RemoteBaseline | None:
        """`None` if this prompt has never been gated yet."""
        ...

    async def get_gate_decision(self, credential: str, run_id: UUID) -> RemoteGateDecision | None:
        """`None` if this run has never been gated yet."""
        ...

    async def get_latency_anomaly(self) -> RemoteLatencyAnomaly:
        """No credential — Regression Detection's latency-anomaly check
        is itself unauthenticated (see its ADR-0004 precedent)."""
        ...


class ReportReader(Protocol):
    async def list_reports(
        self, credential: str, *, experiment_id: UUID | None = None
    ) -> list[RemoteReport]: ...

    async def get_report(self, credential: str, report_id: UUID) -> RemoteReport:
        """Raises `dashboard_backend.domain.errors.ReportNotFoundError`
        on a 404."""
        ...


class NotificationReader(Protocol):
    async def list_channels(self, credential: str) -> list[RemoteChannel]: ...

    async def list_notifications(
        self, credential: str, *, channel_id: UUID | None = None
    ) -> list[RemoteNotification]: ...


class GitHubChecksReader(Protocol):
    async def list_checks(
        self, credential: str, *, repo: str | None = None, commit_sha: str | None = None
    ) -> list[RemoteCheckRun]: ...


class TraceReader(Protocol):
    async def list_recent_traces(self, limit: int) -> list[RemoteTraceSummary]:
        """No credential — the Trace Collector's query API is open (see
        its ADR-0004)."""
        ...
