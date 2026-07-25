from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from prompt_registry.domain.entities import PromptVersion
from prompt_registry.domain.errors import PromptNotFoundError
from prompt_registry.domain.ports import PromptRepository, PromptVersionRepository


class CreateVersionUseCase:
    def __init__(self, prompt_repo: PromptRepository, version_repo: PromptVersionRepository) -> None:
        self._prompt_repo = prompt_repo
        self._version_repo = version_repo

    async def execute(
        self,
        *,
        org_id: UUID,
        prompt_id: UUID,
        template: str,
        variables_schema: dict[str, Any] | None = None,
        semver_tag: str | None = None,
    ) -> PromptVersion:
        prompt = await self._prompt_repo.get_by_id(prompt_id)
        if prompt is None or prompt.org_id != org_id:
            raise PromptNotFoundError(prompt_id)

        version = PromptVersion(
            id=uuid4(),
            prompt_id=prompt_id,
            template=template,
            variables_schema=variables_schema or {},
            semver_tag=semver_tag,
            created_at=datetime.now(UTC),
        )
        await self._version_repo.create(version)
        return version
