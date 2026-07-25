from __future__ import annotations

from uuid import UUID

from regression_detection.domain.entities import Baseline
from regression_detection.domain.errors import BaselineNotFoundError
from regression_detection.domain.ports import BaselineRepository


class GetBaselineUseCase:
    def __init__(self, baseline_repo: BaselineRepository) -> None:
        self._baseline_repo = baseline_repo

    async def execute(self, *, org_id: UUID, prompt_id: UUID) -> Baseline:
        baseline = await self._baseline_repo.get_by_prompt(org_id, prompt_id)
        if baseline is None:
            raise BaselineNotFoundError(prompt_id)
        return baseline
