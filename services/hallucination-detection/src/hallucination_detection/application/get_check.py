from __future__ import annotations

from uuid import UUID

from hallucination_detection.domain.entities import FaithfulnessCheck
from hallucination_detection.domain.errors import FaithfulnessCheckNotFoundError
from hallucination_detection.domain.ports import FaithfulnessCheckRepository


class GetCheckUseCase:
    def __init__(self, repo: FaithfulnessCheckRepository) -> None:
        self._repo = repo

    async def execute(self, *, org_id: UUID, check_id: UUID) -> FaithfulnessCheck:
        check = await self._repo.get_by_id(check_id)
        if check is None or check.org_id != org_id:
            raise FaithfulnessCheckNotFoundError(check_id)
        return check
