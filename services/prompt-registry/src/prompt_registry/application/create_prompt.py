from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from prompt_registry.domain.entities import Prompt
from prompt_registry.domain.errors import DuplicatePromptNameError
from prompt_registry.domain.ports import PromptRepository


class CreatePromptUseCase:
    def __init__(self, prompt_repo: PromptRepository) -> None:
        self._prompt_repo = prompt_repo

    async def execute(self, *, org_id: UUID, name: str) -> Prompt:
        if await self._prompt_repo.get_by_org_and_name(org_id, name) is not None:
            raise DuplicatePromptNameError(name)

        prompt = Prompt(id=uuid4(), org_id=org_id, name=name, created_at=datetime.now(UTC))
        await self._prompt_repo.create(prompt)
        return prompt
