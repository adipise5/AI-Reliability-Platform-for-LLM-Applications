"""Domain entities for the GitHub Integration service — see ADR-0001: no
framework imports here.

A `CheckRun` starts life when a `pull_request` webhook fires (created in
GitHub as `queued`, before any eval run even exists yet — see
`HandleWebhookUseCase`) and finishes when the CI workflow calls back with
a completed eval run's id (`CompleteCheckUseCase`), at which point this
service asks Regression Detection for that run's gate decision and
translates its verdict into a GitHub check conclusion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class CheckStatus(StrEnum):
    QUEUED = "queued"
    COMPLETED = "completed"


class CheckConclusion(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class CheckRun:
    id: UUID
    org_id: UUID
    repo: str
    commit_sha: str
    github_check_run_id: int
    status: CheckStatus
    created_at: datetime
    conclusion: CheckConclusion | None = None
    run_id: UUID | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RemoteGateDecision:
    run_id: UUID
    verdict: str
    observed_score: float
    baseline_mean: float
    baseline_stddev: float
