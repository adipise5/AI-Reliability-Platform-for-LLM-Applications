"""Ports: interfaces the application layer depends on.

`PromptRegistryPort`, `DatasetPort`, and `GatewayPort` are HTTP clients to
other bounded contexts, modeled as ports for the same reason a database
repository is: the application layer shouldn't know it's httpx underneath,
and a fake makes the orchestration logic in `execute_run.py` testable
without three other services running.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from evaluation_engine.domain.entities import (
    EvalRun,
    RemoteCompletion,
    RemoteDatasetItem,
    RemotePromptVersion,
    RunItemResult,
    Score,
)


class EvalRunRepository(Protocol):
    async def create(self, run: EvalRun) -> None: ...

    async def get_by_id(self, run_id: UUID) -> EvalRun | None: ...

    async def update(self, run: EvalRun) -> None:
        """Persists the full row — callers read-modify-write via
        `dataclasses.replace`, since `EvalRun` is immutable."""
        ...

    async def list_by_org(
        self, org_id: UUID, *, prompt_id: UUID | None = None, dataset_id: UUID | None = None
    ) -> list[EvalRun]:
        """Ordered most-recent-first. `prompt_id`/`dataset_id` narrow the
        list — Experiment Tracking's score-history view is exactly "every
        run for this prompt, over time"."""
        ...


class RunItemResultRepository(Protocol):
    async def create(self, result: RunItemResult) -> None: ...

    async def list_by_run(self, run_id: UUID) -> list[RunItemResult]: ...


class PromptRegistryPort(Protocol):
    async def get_version(
        self, credential: str, *, prompt_id: UUID, version_id: UUID
    ) -> RemotePromptVersion: ...


class DatasetPort(Protocol):
    async def get_items(
        self, credential: str, *, dataset_id: UUID, version: int | None
    ) -> tuple[int, list[RemoteDatasetItem]]:
        """Returns `(resolved_version, items)` — `version=None` means "the
        current version," and the caller finds out which one that was."""
        ...


class GatewayPort(Protocol):
    async def complete(
        self,
        credential: str,
        *,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int | None,
    ) -> RemoteCompletion:
        """Sends `prompt` as a single user-role message — Prompt Registry
        templates are one rendered string, not separate system/user
        parts, so there's nothing to split here yet."""
        ...


class HallucinationDetectionPort(Protocol):
    async def check_faithfulness(
        self, credential: str, *, model: str, response: str, context: str
    ) -> tuple[float, int]:
        """Returns `(faithfulness_score, claim_count)` from the
        Hallucination Detection service's claim-extraction-and-
        verification check."""
        ...


class Scorer(Protocol):
    name: str

    async def score(
        self, *, credential: str, output: str, expected_output: object, context: dict[str, object]
    ) -> Score:
        """`credential` is passed through, not stored — an LLM-judge scorer
        needs it to call the Gateway; a deterministic scorer just ignores
        it."""
        ...


class ScorerRegistry(Protocol):
    def get(self, name: str) -> Scorer:
        """Raises `evaluation_engine.domain.errors.UnknownScorerError` if
        `name` isn't registered."""
        ...


class TaskQueue(Protocol):
    def enqueue_run(self, run_id: UUID, credential: str) -> None:
        """`credential` is never persisted to the database — see the
        service README's "Auth for background execution" section. It
        lives only in the queue message."""
        ...
