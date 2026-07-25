"""Use case: one run, with its regression gate decision merged in — the
one place besides the overview where this service actually combines two
upstream services into a single response rather than just passing one
through.
"""

from __future__ import annotations

from uuid import UUID

from dashboard_backend.domain.entities import RunDetail
from dashboard_backend.domain.ports import EvalRunReader, RegressionReader


class GetRunDetailUseCase:
    def __init__(self, eval_run_reader: EvalRunReader, regression_reader: RegressionReader) -> None:
        self._eval_run_reader = eval_run_reader
        self._regression_reader = regression_reader

    async def execute(self, *, credential: str, run_id: UUID) -> RunDetail:
        run, items = await self._eval_run_reader.get_run(credential, run_id)
        gate_decision = await self._regression_reader.get_gate_decision(credential, run_id)
        return RunDetail(run=run, items=items, gate_decision=gate_decision)
