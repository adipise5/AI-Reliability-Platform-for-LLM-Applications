from __future__ import annotations

from uuid import UUID

from evaluation_engine.domain.entities import EvalRun
from evaluation_engine.domain.ports import EvalRunRepository


class ListRunsUseCase:
    """The read side Experiment Tracking (Week 8) is built on — see
    ADR-0005: it aggregates across runs rather than owning a copy of
    them, so it needs to enumerate runs by prompt/dataset here."""

    def __init__(self, eval_run_repo: EvalRunRepository) -> None:
        self._eval_run_repo = eval_run_repo

    async def execute(
        self, *, org_id: UUID, prompt_id: UUID | None = None, dataset_id: UUID | None = None
    ) -> list[EvalRun]:
        return await self._eval_run_repo.list_by_org(
            org_id, prompt_id=prompt_id, dataset_id=dataset_id
        )
