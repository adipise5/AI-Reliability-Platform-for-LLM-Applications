from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from gateway.api.routers import chat, health
from gateway.api.schemas import ErrorOut
from gateway.domain.errors import (
    AuthenticationError,
    GatewayError,
    ProviderRequestError,
    UnsupportedModelError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Gateway",
        version="0.1.0",
        description="Unified chat-completion API across Claude, GPT, Gemini, and Ollama.",
    )

    app.include_router(health.router)
    app.include_router(chat.router)

    @app.exception_handler(UnsupportedModelError)
    async def _unsupported_model(_: Request, exc: UnsupportedModelError) -> JSONResponse:
        body = ErrorOut(type="unsupported_model", message=str(exc), retryable=False)
        return JSONResponse(status_code=400, content=body.model_dump())

    @app.exception_handler(AuthenticationError)
    async def _authentication_error(_: Request, exc: AuthenticationError) -> JSONResponse:
        body = ErrorOut(type="authentication_error", message=str(exc), retryable=False)
        return JSONResponse(status_code=401, content=body.model_dump())

    @app.exception_handler(ProviderRequestError)
    async def _provider_error(_: Request, exc: ProviderRequestError) -> JSONResponse:
        body = ErrorOut(type="provider_error", message=str(exc), retryable=exc.retryable)
        return JSONResponse(status_code=502, content=body.model_dump())

    @app.exception_handler(GatewayError)
    async def _gateway_error(_: Request, exc: GatewayError) -> JSONResponse:
        body = ErrorOut(type="gateway_error", message=str(exc), retryable=False)
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
