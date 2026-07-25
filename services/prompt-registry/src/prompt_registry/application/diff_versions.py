from __future__ import annotations

import difflib
from uuid import UUID

from prompt_registry.domain.entities import VersionDiff
from prompt_registry.domain.errors import PromptNotFoundError, PromptVersionNotFoundError
from prompt_registry.domain.ports import PromptRepository, PromptVersionRepository


class DiffVersionsUseCase:
    def __init__(self, prompt_repo: PromptRepository, version_repo: PromptVersionRepository) -> None:
        self._prompt_repo = prompt_repo
        self._version_repo = version_repo

    async def execute(
        self, *, org_id: UUID, prompt_id: UUID, version_a_id: UUID, version_b_id: UUID
    ) -> VersionDiff:
        prompt = await self._prompt_repo.get_by_id(prompt_id)
        if prompt is None or prompt.org_id != org_id:
            raise PromptNotFoundError(prompt_id)

        version_a = await self._version_repo.get_by_id(version_a_id)
        version_b = await self._version_repo.get_by_id(version_b_id)
        for version, version_id in ((version_a, version_a_id), (version_b, version_b_id)):
            if version is None or version.prompt_id != prompt_id:
                raise PromptVersionNotFoundError(version_id)
        assert version_a is not None and version_b is not None  # narrowed by the loop above

        diff = difflib.unified_diff(
            version_a.template.splitlines(),
            version_b.template.splitlines(),
            fromfile=str(version_a_id),
            tofile=str(version_b_id),
            lineterm="",
        )
        return VersionDiff(version_a=version_a_id, version_b=version_b_id, unified_diff=tuple(diff))
