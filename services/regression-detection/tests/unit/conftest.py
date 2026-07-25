from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from regression_detection.domain.entities import Baseline, GateDecision, RemoteEvalRun, RemoteTraceSummary
from regression_detection.domain.errors import UpstreamServiceError


class FakeBaselineRepository:
    def __init__(self, seed: list[Baseline] | None = None) -> None:
        self.baselines: dict[tuple[UUID, UUID], Baseline] = {
            (b.org_id, b.prompt_id): b for b in (seed or [])
        }
        self.upsert_calls: list[Baseline] = []

    async def upsert(self, baseline: Baseline) -> Baseline:
        self.upsert_calls.append(baseline)
        self.baselines[(baseline.org_id, baseline.prompt_id)] = baseline
        return baseline

    async def get_by_prompt(self, org_id: UUID, prompt_id: UUID) -> Baseline | None:
        return self.baselines.get((org_id, prompt_id))


class FakeGateDecisionRepository:
    def __init__(self) -> None:
        self.decisions: list[GateDecision] = []

    async def create(self, decision: GateDecision) -> None:
        self.decisions.append(decision)

    async def get_latest_for_run(self, run_id: UUID) -> GateDecision | None:
        matching = [d for d in self.decisions if d.run_id == run_id]
        if not matching:
            return None
        return max(matching, key=lambda d: d.created_at)


class FakeEvalRunReader:
    def __init__(self, runs: dict[UUID, RemoteEvalRun] | None = None) -> None:
        self.runs = runs or {}
        self.get_run_calls: list[UUID] = []
        self.list_runs_calls: list[UUID] = []

    async def get_run(self, credential: str, run_id: UUID) -> RemoteEvalRun:
        self.get_run_calls.append(run_id)
        if run_id not in self.runs:
            raise UpstreamServiceError("evaluation-engine", f"no run {run_id}")
        return self.runs[run_id]

    async def list_runs(self, credential: str, *, prompt_id: UUID) -> list[RemoteEvalRun]:
        self.list_runs_calls.append(prompt_id)
        return [r for r in self.runs.values() if r.prompt_id == prompt_id]


class FakeTraceReader:
    def __init__(self, traces: list[RemoteTraceSummary] | None = None) -> None:
        self.traces = traces or []

    async def list_recent_traces(self, limit: int) -> list[RemoteTraceSummary]:
        return self.traces[:limit]


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


def make_run(**overrides: object) -> RemoteEvalRun:
    base = RemoteEvalRun(id=uuid4(), prompt_id=uuid4(), status="completed", aggregate_score=0.9)
    return replace(base, **overrides)


def make_trace(**overrides: object) -> RemoteTraceSummary:
    base = RemoteTraceSummary(trace_id=uuid4().hex, status="OK", duration_ms=100.0)
    return replace(base, **overrides)


def make_baseline(**overrides: object) -> Baseline:
    base = Baseline(
        id=uuid4(),
        org_id=uuid4(),
        prompt_id=uuid4(),
        mean_score=0.9,
        stddev_score=0.05,
        sample_size=5,
        updated_at=datetime.now(UTC),
    )
    return replace(base, **overrides)
