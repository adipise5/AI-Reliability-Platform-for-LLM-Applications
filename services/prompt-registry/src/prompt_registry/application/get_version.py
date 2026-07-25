from __future__ import annotations

from uuid import UUID

from prompt_registry.domain.entities import PromptVersion
from prompt_registry.domain.errors import PromptNotFoundError, PromptVersionNotFoundError
from prompt_registry.domain.ports import PromptRepository, PromptVersionRepository


class GetVersionUseCase:
    """Fetches one exact version by id — what the Evaluation Engine pins
    an eval run to, as opposed to `GetActiveVersionUseCase`'s "whatever is
    promoted right now"."""

    def __init__(self, prompt_repo: PromptRepository, version_repo: PromptVersionRepository) -> None:
        self._prompt_repo = prompt_repo
        self._version_repo = version_repo

    async def execute(self, *, org_id: UUID, prompt_id: UUID, version_id: UUID) -> PromptVersion:
        prompt = await self._prompt_repo.get_by_id(prompt_id)
        if prompt is None or prompt.org_id != org_id:
            raise PromptNotFoundError(prompt_id)

        version = await self._version_repo.get_by_id(version_id)
        if version is None or version.prompt_id != prompt_id:
            raise PromptVersionNotFoundError(version_id)
        return version
