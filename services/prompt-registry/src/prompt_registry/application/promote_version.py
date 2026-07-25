from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from prompt_registry.domain.entities import PromotionEvent
from prompt_registry.domain.errors import PromptNotFoundError, PromptVersionNotFoundError
from prompt_registry.domain.ports import PromotionRepository, PromptRepository, PromptVersionRepository


class PromoteVersionUseCase:
    def __init__(
        self,
        prompt_repo: PromptRepository,
        version_repo: PromptVersionRepository,
        promotion_repo: PromotionRepository,
    ) -> None:
        self._prompt_repo = prompt_repo
        self._version_repo = version_repo
        self._promotion_repo = promotion_repo

    async def execute(
        self, *, org_id: UUID, prompt_id: UUID, version_id: UUID, environment: str
    ) -> PromotionEvent:
        prompt = await self._prompt_repo.get_by_id(prompt_id)
        if prompt is None or prompt.org_id != org_id:
            raise PromptNotFoundError(prompt_id)

        version = await self._version_repo.get_by_id(version_id)
        if version is None or version.prompt_id != prompt_id:
            raise PromptVersionNotFoundError(version_id)

        event = PromotionEvent(
            id=uuid4(),
            prompt_id=prompt_id,
            version_id=version_id,
            environment=environment,
            created_at=datetime.now(UTC),
        )
        await self._promotion_repo.create(event)
        return event
