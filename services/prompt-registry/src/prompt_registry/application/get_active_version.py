from __future__ import annotations

from uuid import UUID

from prompt_registry.domain.entities import PromptVersion
from prompt_registry.domain.errors import NoActiveVersionError, PromptNotFoundError
from prompt_registry.domain.ports import PromotionRepository, PromptRepository, PromptVersionRepository


class GetActiveVersionUseCase:
    def __init__(
        self,
        prompt_repo: PromptRepository,
        version_repo: PromptVersionRepository,
        promotion_repo: PromotionRepository,
    ) -> None:
        self._prompt_repo = prompt_repo
        self._version_repo = version_repo
        self._promotion_repo = promotion_repo

    async def execute(self, *, org_id: UUID, prompt_id: UUID, environment: str) -> PromptVersion:
        prompt = await self._prompt_repo.get_by_id(prompt_id)
        if prompt is None or prompt.org_id != org_id:
            raise PromptNotFoundError(prompt_id)

        event = await self._promotion_repo.get_active(prompt_id, environment)
        if event is None:
            raise NoActiveVersionError(prompt_id, environment)

        version = await self._version_repo.get_by_id(event.version_id)
        assert version is not None, "a promoted version was deleted — repositories must not allow this"
        return version
