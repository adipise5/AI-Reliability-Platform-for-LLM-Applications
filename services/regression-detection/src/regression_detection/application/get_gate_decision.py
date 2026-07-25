from __future__ import annotations

from uuid import UUID

from regression_detection.domain.entities import GateDecision
from regression_detection.domain.errors import GateDecisionNotFoundError
from regression_detection.domain.ports import GateDecisionRepository


class GetGateDecisionUseCase:
    def __init__(self, gate_decision_repo: GateDecisionRepository) -> None:
        self._gate_decision_repo = gate_decision_repo

    async def execute(self, *, org_id: UUID, run_id: UUID) -> GateDecision:
        decision = await self._gate_decision_repo.get_latest_for_run(run_id)
        if decision is None or decision.org_id != org_id:
            raise GateDecisionNotFoundError(run_id)
        return decision
