from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from prompt_registry.domain.entities import PromotionEvent, Prompt, PromptVersion, VersionDiff


class CreatePromptIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class PromptOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    created_at: datetime

    @classmethod
    def from_domain(cls, prompt: Prompt) -> PromptOut:
        return cls(id=prompt.id, org_id=prompt.org_id, name=prompt.name, created_at=prompt.created_at)


class CreateVersionIn(BaseModel):
    template: str = Field(..., min_length=1)
    variables_schema: dict[str, Any] | None = None
    semver_tag: str | None = None


class PromptVersionOut(BaseModel):
    id: UUID
    prompt_id: UUID
    template: str
    variables_schema: dict[str, Any]
    semver_tag: str | None
    created_at: datetime

    @classmethod
    def from_domain(cls, version: PromptVersion) -> PromptVersionOut:
        return cls(
            id=version.id,
            prompt_id=version.prompt_id,
            template=version.template,
            variables_schema=version.variables_schema,
            semver_tag=version.semver_tag,
            created_at=version.created_at,
        )


class PromoteVersionIn(BaseModel):
    version_id: UUID
    environment: str = Field(..., min_length=1, max_length=50)


class PromotionOut(BaseModel):
    id: UUID
    prompt_id: UUID
    version_id: UUID
    environment: str
    created_at: datetime

    @classmethod
    def from_domain(cls, event: PromotionEvent) -> PromotionOut:
        return cls(
            id=event.id,
            prompt_id=event.prompt_id,
            version_id=event.version_id,
            environment=event.environment,
            created_at=event.created_at,
        )


class VersionDiffOut(BaseModel):
    version_a: UUID
    version_b: UUID
    unified_diff: list[str]

    @classmethod
    def from_domain(cls, diff: VersionDiff) -> VersionDiffOut:
        return cls(
            version_a=diff.version_a, version_b=diff.version_b, unified_diff=list(diff.unified_diff)
        )


class ErrorOut(BaseModel):
    type: str
    message: str
