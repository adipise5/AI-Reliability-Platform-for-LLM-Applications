"""Use case: create an eval run and hand it to the task queue.

Deliberately does no upstream validation (that the prompt version or
dataset actually exist, say) before enqueueing — that would mean this
synchronous, fast endpoint making network calls to two other services on
every trigger. `ExecuteEvalRunUseCase` validates all of that when the run
actually executes and fails the run with a clear error if not; the run
record itself (status=PENDING) is the receipt that the trigger succeeded.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from evaluation_engine.domain.entities import EvalRun, RunStatus
from evaluation_engine.domain.ports import EvalRunRepository, TaskQueue

DEFAULT_SCORERS: tuple[str, ...] = ("exact_match",)


class TriggerEvalRunUseCase:
    def __init__(self, eval_run_repo: EvalRunRepository, task_queue: TaskQueue) -> None:
        self._eval_run_repo = eval_run_repo
        self._task_queue = task_queue

    async def execute(
        self,
        *,
        org_id: UUID,
        prompt_id: UUID,
        prompt_version_id: UUID,
        dataset_id: UUID,
        model: str,
        credential: str,
        dataset_version: int | None = None,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        scorer_names: tuple[str, ...] | None = None,
    ) -> EvalRun:
        run = EvalRun(
            id=uuid4(),
            org_id=org_id,
            prompt_id=prompt_id,
            prompt_version_id=prompt_version_id,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            scorer_names=scorer_names or DEFAULT_SCORERS,
            status=RunStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        await self._eval_run_repo.create(run)
        self._task_queue.enqueue_run(run.id, credential)
        return run
