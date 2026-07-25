from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from evaluation_engine.domain.entities import (
    EvalRun,
    RemoteCompletion,
    RemoteDatasetItem,
    RemotePromptVersion,
    RunItemResult,
    RunStatus,
)
from evaluation_engine.domain.errors import UpstreamServiceError


class FakeEvalRunRepository:
    def __init__(self, seed: list[EvalRun] | None = None) -> None:
        self.runs: dict[UUID, EvalRun] = {r.id: r for r in (seed or [])}

    async def create(self, run: EvalRun) -> None:
        self.runs[run.id] = run

    async def get_by_id(self, run_id: UUID) -> EvalRun | None:
        return self.runs.get(run_id)

    async def update(self, run: EvalRun) -> None:
        self.runs[run.id] = run

    async def list_by_org(
        self, org_id: UUID, *, prompt_id: UUID | None = None, dataset_id: UUID | None = None
    ) -> list[EvalRun]:
        matches = [r for r in self.runs.values() if r.org_id == org_id]
        if prompt_id is not None:
            matches = [r for r in matches if r.prompt_id == prompt_id]
        if dataset_id is not None:
            matches = [r for r in matches if r.dataset_id == dataset_id]
        return sorted(matches, key=lambda r: r.created_at, reverse=True)


class FakeRunItemResultRepository:
    def __init__(self) -> None:
        self.results: list[RunItemResult] = []

    async def create(self, result: RunItemResult) -> None:
        self.results.append(result)

    async def list_by_run(self, run_id: UUID) -> list[RunItemResult]:
        return [r for r in self.results if r.run_id == run_id]


class FakePromptRegistryClient:
    def __init__(self, version: RemotePromptVersion | None = None) -> None:
        self._version = version

    async def get_version(
        self, credential: str, *, prompt_id: UUID, version_id: UUID
    ) -> RemotePromptVersion:
        if self._version is None:
            raise UpstreamServiceError("prompt-registry", "404: not found")
        return self._version


class FakeDatasetClient:
    def __init__(self, items: list[RemoteDatasetItem], *, resolved_version: int = 1) -> None:
        self._items = items
        self._resolved_version = resolved_version

    async def get_items(
        self, credential: str, *, dataset_id: UUID, version: int | None
    ) -> tuple[int, list[RemoteDatasetItem]]:
        return self._resolved_version, self._items


class FakeGatewayClient:
    def __init__(self, completion: RemoteCompletion | None = None) -> None:
        self._completion = completion or RemoteCompletion(
            content="42", prompt_tokens=5, completion_tokens=1, latency_ms=10.0
        )
        self.calls: list[dict[str, object]] = []

    async def complete(
        self, credential: str, *, model: str, prompt: str, temperature: float, max_tokens: int | None
    ) -> RemoteCompletion:
        self.calls.append({"model": model, "prompt": prompt, "temperature": temperature})
        return self._completion


class FakeTaskQueue:
    def __init__(self) -> None:
        self.enqueued: list[tuple[UUID, str]] = []

    def enqueue_run(self, run_id: UUID, credential: str) -> None:
        self.enqueued.append((run_id, credential))


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_run(org_id: UUID) -> EvalRun:
    from datetime import UTC, datetime

    return EvalRun(
        id=uuid4(),
        org_id=org_id,
        prompt_id=uuid4(),
        prompt_version_id=uuid4(),
        dataset_id=uuid4(),
        model="claude-sonnet-5",
        scorer_names=("exact_match",),
        status=RunStatus.PENDING,
        created_at=datetime.now(UTC),
    )


def make_pending_run(**overrides: object) -> EvalRun:
    from datetime import UTC, datetime

    base = EvalRun(
        id=uuid4(),
        org_id=uuid4(),
        prompt_id=uuid4(),
        prompt_version_id=uuid4(),
        dataset_id=uuid4(),
        model="claude-sonnet-5",
        scorer_names=("exact_match",),
        status=RunStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    return replace(base, **overrides)
