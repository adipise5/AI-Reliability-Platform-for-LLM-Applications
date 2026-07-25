from __future__ import annotations

from typing import Protocol
from uuid import UUID

from regression_detection.domain.entities import Baseline, GateDecision, RemoteEvalRun, RemoteTraceSummary


class BaselineRepository(Protocol):
    async def upsert(self, baseline: Baseline) -> Baseline:
        """One baseline per `(org_id, prompt_id)` — replaces whatever was
        there, since it's always meant to reflect "every completed run as
        of the last gate check," not an append-only history."""
        ...

    async def get_by_prompt(self, org_id: UUID, prompt_id: UUID) -> Baseline | None: ...


class GateDecisionRepository(Protocol):
    async def create(self, decision: GateDecision) -> None:
        """Append-only — re-gating a run records a new decision rather
        than overwriting the last one, so the history of *why* a run
        passed or failed over time is never lost."""
        ...

    async def get_latest_for_run(self, run_id: UUID) -> GateDecision | None: ...


class EvalRunReader(Protocol):
    async def get_run(self, credential: str, run_id: UUID) -> RemoteEvalRun:
        """Raises `regression_detection.domain.errors.UpstreamServiceError`
        if the Evaluation Engine 404s or otherwise fails."""
        ...

    async def list_runs(self, credential: str, *, prompt_id: UUID) -> list[RemoteEvalRun]: ...


class TraceReader(Protocol):
    async def list_recent_traces(self, limit: int) -> list[RemoteTraceSummary]:
        """No credential — the Trace Collector's query API is open (see
        ADR-0004); there's no org to scope by yet."""
        ...
