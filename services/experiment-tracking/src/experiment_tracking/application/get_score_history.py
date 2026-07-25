"""Use case: score history for a prompt over time — a pure passthrough to
the Evaluation Engine's own list endpoint, no local storage involved at
all. This is the clearest illustration of ADR-0005's "aggregation layer,
not a second store" framing."""

from __future__ import annotations

from uuid import UUID

from experiment_tracking.domain.entities import RemoteEvalRunSummary
from experiment_tracking.domain.ports import EvalRunReader


class GetScoreHistoryUseCase:
    def __init__(self, eval_run_reader: EvalRunReader) -> None:
        self._eval_run_reader = eval_run_reader

    async def execute(self, *, credential: str, prompt_id: UUID) -> list[RemoteEvalRunSummary]:
        return await self._eval_run_reader.list_runs(credential, prompt_id=prompt_id)
