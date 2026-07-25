from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from gateway.api.deps import (
    get_provider_registry,
    get_route_chat_use_case,
    get_stream_chat_use_case,
    require_chat_scope,
)
from gateway.api.schemas import ChatChunkOut, ChatRequestIn, ChatResponseOut, ErrorOut
from gateway.application.route_chat import RouteChatUseCase
from gateway.application.stream_chat import StreamChatUseCase
from gateway.domain.entities import AuthContext
from gateway.domain.errors import ProviderRequestError
from gateway.domain.ports import ProviderRegistry

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponseOut)
async def create_chat_completion(
    payload: ChatRequestIn,
    auth: Annotated[AuthContext, Depends(require_chat_scope)],
    use_case: Annotated[RouteChatUseCase, Depends(get_route_chat_use_case)],
) -> ChatResponseOut:
    response = await use_case.execute(payload.to_domain(), org_id=auth.org_id)
    return ChatResponseOut.from_domain(response)


@router.post("/stream")
async def stream_chat_completion(
    payload: ChatRequestIn,
    auth: Annotated[AuthContext, Depends(require_chat_scope)],
    use_case: Annotated[StreamChatUseCase, Depends(get_stream_chat_use_case)],
    registry: Annotated[ProviderRegistry, Depends(get_provider_registry)],
) -> StreamingResponse:
    domain_request = payload.to_domain()
    # Resolve the provider *before* opening the stream: once StreamingResponse
    # starts, the 200 status line is already on the wire, so an
    # UnsupportedModelError raised from inside the generator could no longer
    # be reported as a 4xx. Failing fast here keeps that error path a normal
    # HTTP error response instead of a mid-stream SSE error event.
    registry.resolve(domain_request.model)

    async def event_source() -> AsyncIterator[str]:
        try:
            async for chunk in use_case.execute(domain_request, org_id=auth.org_id):
                yield f"data: {ChatChunkOut.from_domain(chunk).model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
        except ProviderRequestError as exc:
            error = ErrorOut(type="provider_error", message=str(exc), retryable=exc.retryable)
            yield f"event: error\ndata: {error.model_dump_json()}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")
