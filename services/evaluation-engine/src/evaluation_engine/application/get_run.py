from __future__ import annotations

from uuid import UUID

from evaluation_engine.domain.entities import EvalRun, RunItemResult
from evaluation_engine.domain.errors import EvalRunNotFoundError
from evaluation_engine.domain.ports import EvalRunRepository, RunItemResultRepository


class GetEvalRunUseCase:
    def __init__(self, eval_run_repo: EvalRunRepository, item_repo: RunItemResultRepository) -> None:
        self._eval_run_repo = eval_run_repo
        self._item_repo = item_repo

    async def execute(self, *, org_id: UUID, run_id: UUID) -> tuple[EvalRun, list[RunItemResult]]:
        run = await self._eval_run_repo.get_by_id(run_id)
        if run is None or run.org_id != org_id:
            raise EvalRunNotFoundError(run_id)

        items = await self._item_repo.list_by_run(run_id)
        return run, items
