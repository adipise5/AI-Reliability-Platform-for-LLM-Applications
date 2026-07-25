"""API-facing request/response models.

Kept separate from `domain/entities.py` on purpose: these are a wire
contract (snake_case JSON, OpenAPI-documented, versioned by the route path)
and are free to evolve independently of the internal domain model.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from gateway.domain.entities import ChatChunk, ChatMessage, ChatRequest, ChatResponse, Role


class ChatMessageIn(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequestIn(BaseModel):
    model: str = Field(..., examples=["claude-sonnet-5", "gpt-5", "gemini-2.5-pro", "llama3.1"])
    messages: list[ChatMessageIn] = Field(..., min_length=1)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)

    def to_domain(self) -> ChatRequest:
        return ChatRequest(
            model=self.model,
            messages=tuple(ChatMessage(role=Role(m.role), content=m.content) for m in self.messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


class UsageOut(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponseOut(BaseModel):
    provider: str
    model: str
    content: str
    finish_reason: str
    usage: UsageOut
    latency_ms: float

    @classmethod
    def from_domain(cls, response: ChatResponse) -> ChatResponseOut:
        return cls(
            provider=response.provider.value,
            model=response.model,
            content=response.content,
            finish_reason=response.finish_reason,
            usage=UsageOut(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            latency_ms=response.latency_ms,
        )


class ChatChunkOut(BaseModel):
    delta: str
    finish_reason: str | None = None
    usage: UsageOut | None = None

    @classmethod
    def from_domain(cls, chunk: ChatChunk) -> ChatChunkOut:
        return cls(
            delta=chunk.delta,
            finish_reason=chunk.finish_reason,
            usage=(
                UsageOut(
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    total_tokens=chunk.usage.total_tokens,
                )
                if chunk.usage
                else None
            ),
        )


class ErrorOut(BaseModel):
    type: str
    message: str
    retryable: bool = False
