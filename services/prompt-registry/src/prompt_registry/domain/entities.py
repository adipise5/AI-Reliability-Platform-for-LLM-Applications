"""Domain entities for the Prompt Registry — see ADR-0001: no framework
imports here, `uuid`/`datetime` are standard library."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Prompt:
    id: UUID
    org_id: UUID
    name: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PromptVersion:
    """An immutable template snapshot. Consumers (e.g. the Gateway,
    Evaluation Engine) reference versions by `id`, never by "latest" —
    reproducible eval runs depend on this."""

    id: UUID
    prompt_id: UUID
    template: str
    variables_schema: dict[str, Any] = field(default_factory=dict)
    semver_tag: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, slots=True)
class PromotionEvent:
    """Append-only: "environment X points at version Y as of now." The
    active version for an environment is whichever promotion for that
    (prompt_id, environment) pair happened most recently — there's no
    separate "current pointer" row to keep in sync."""

    id: UUID
    prompt_id: UUID
    version_id: UUID
    environment: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class VersionDiff:
    version_a: UUID
    version_b: UUID
    unified_diff: tuple[str, ...]
