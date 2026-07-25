from __future__ import annotations

from typing import Protocol
from uuid import UUID

from prompt_registry.domain.entities import PromotionEvent, Prompt, PromptVersion


class PromptRepository(Protocol):
    async def create(self, prompt: Prompt) -> None: ...

    async def get_by_id(self, prompt_id: UUID) -> Prompt | None: ...

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Prompt | None: ...


class PromptVersionRepository(Protocol):
    async def create(self, version: PromptVersion) -> None: ...

    async def get_by_id(self, version_id: UUID) -> PromptVersion | None: ...

    async def list_by_prompt(self, prompt_id: UUID) -> list[PromptVersion]: ...


class PromotionRepository(Protocol):
    async def create(self, event: PromotionEvent) -> None: ...

    async def get_active(self, prompt_id: UUID, environment: str) -> PromotionEvent | None:
        """Returns the most recent promotion for (prompt_id, environment),
        or None if nothing has ever been promoted there."""
        ...
