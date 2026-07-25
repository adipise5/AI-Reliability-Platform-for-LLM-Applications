from __future__ import annotations

from dashboard_backend.domain.entities import RemoteEvalRun
from dashboard_backend.domain.ports import EvalRunReader


class ListRunsUseCase:
    def __init__(self, eval_run_reader: EvalRunReader) -> None:
        self._eval_run_reader = eval_run_reader

    async def execute(self, *, credential: str) -> list[RemoteEvalRun]:
        return await self._eval_run_reader.list_runs(credential)
