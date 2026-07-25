from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from prompt_registry.domain.entities import PromotionEvent, Prompt, PromptVersion


class FakePromptRepository:
    def __init__(self, seed: list[Prompt] | None = None) -> None:
        self.prompts: dict[UUID, Prompt] = {p.id: p for p in (seed or [])}

    async def create(self, prompt: Prompt) -> None:
        self.prompts[prompt.id] = prompt

    async def get_by_id(self, prompt_id: UUID) -> Prompt | None:
        return self.prompts.get(prompt_id)

    async def get_by_org_and_name(self, org_id: UUID, name: str) -> Prompt | None:
        return next(
            (p for p in self.prompts.values() if p.org_id == org_id and p.name == name), None
        )


class FakePromptVersionRepository:
    def __init__(self, seed: list[PromptVersion] | None = None) -> None:
        self.versions: dict[UUID, PromptVersion] = {v.id: v for v in (seed or [])}

    async def create(self, version: PromptVersion) -> None:
        self.versions[version.id] = version

    async def get_by_id(self, version_id: UUID) -> PromptVersion | None:
        return self.versions.get(version_id)

    async def list_by_prompt(self, prompt_id: UUID) -> list[PromptVersion]:
        return sorted(
            (v for v in self.versions.values() if v.prompt_id == prompt_id),
            key=lambda v: v.created_at,
        )


class FakePromotionRepository:
    def __init__(self, seed: list[PromotionEvent] | None = None) -> None:
        self.events: list[PromotionEvent] = list(seed or [])

    async def create(self, event: PromotionEvent) -> None:
        self.events.append(event)

    async def get_active(self, prompt_id: UUID, environment: str) -> PromotionEvent | None:
        matching = [
            e for e in self.events if e.prompt_id == prompt_id and e.environment == environment
        ]
        return max(matching, key=lambda e: e.created_at) if matching else None


@pytest.fixture
def org_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_prompt(org_id: UUID) -> Prompt:
    from datetime import UTC, datetime

    return Prompt(id=uuid4(), org_id=org_id, name="support-agent", created_at=datetime.now(UTC))
