from __future__ import annotations

from uuid import UUID

from github_integration.domain.entities import CheckRun
from github_integration.domain.errors import CheckNotFoundError
from github_integration.domain.ports import CheckRunRepository


class GetCheckUseCase:
    def __init__(self, check_repo: CheckRunRepository) -> None:
        self._check_repo = check_repo

    async def execute(self, *, org_id: UUID, check_id: UUID) -> CheckRun:
        check = await self._check_repo.get_by_id(check_id)
        if check is None or check.org_id != org_id:
            raise CheckNotFoundError(check_id)
        return check
