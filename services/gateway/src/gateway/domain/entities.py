"""Domain entities and value objects for the AI Gateway.

Nothing in this module may import FastAPI, SQLAlchemy, httpx, or any
provider SDK — see ADR-0001. These are plain, immutable value objects that
the application and infrastructure layers translate to/from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Provider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """A provider-agnostic chat completion request.

    ``model`` is the caller-facing model identifier, e.g. ``"claude-sonnet-5"``
    or ``"gpt-5"``. Provider selection is resolved from this string by the
    application layer's provider registry, never guessed inside a provider
    adapter.
    """

    model: str
    messages: tuple[ChatMessage, ...]
    temperature: float = 1.0
    max_tokens: int | None = None
    stream: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True, slots=True)
class ChatResponse:
    provider: Provider
    model: str
    content: str
    finish_reason: str
    usage: Usage
    latency_ms: float


@dataclass(frozen=True, slots=True)
class ChatChunk:
    """One increment of a streamed response."""

    delta: str
    finish_reason: str | None = None
    usage: Usage | None = None


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Identity attached to a request after successful authentication.

    `org_id` is what Cost Analytics attributes spend to and what a future
    Dashboard would scope trace views by — see ADR-0006 for why it wasn't
    here until Week 9, and why it is now.
    """

    subject: str
    org_id: str
    scopes: frozenset[str] = frozenset()

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes
