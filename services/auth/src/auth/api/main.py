from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from auth.api.routers import api_keys, auth, health, orgs
from auth.api.schemas import ErrorOut
from auth.domain.errors import (
    ApiKeyNotFoundError,
    AuthDomainError,
    EmailAlreadyRegisteredError,
    InsufficientScopeError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from auth.infrastructure.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Authentication Service",
        version="0.1.0",
        description="Orgs, users, API keys, JWTs, and RBAC for the AI Reliability Platform.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Standard request-count/latency histograms at GET /metrics — see
    # docs/deployment.md's Grafana section for the dashboard that reads them.
    Instrumentator().instrument(app).expose(app)

    app.include_router(health.router)
    app.include_router(orgs.router)
    app.include_router(auth.router)
    app.include_router(api_keys.router)

    @app.exception_handler(EmailAlreadyRegisteredError)
    async def _email_taken(_: Request, exc: EmailAlreadyRegisteredError) -> JSONResponse:
        body = ErrorOut(type="email_already_registered", message=str(exc))
        return JSONResponse(status_code=409, content=body.model_dump())

    @app.exception_handler(InvalidCredentialsError)
    async def _invalid_credentials(_: Request, exc: InvalidCredentialsError) -> JSONResponse:
        body = ErrorOut(type="invalid_credentials", message=str(exc))
        return JSONResponse(status_code=401, content=body.model_dump())

    @app.exception_handler(InvalidTokenError)
    async def _invalid_token(_: Request, exc: InvalidTokenError) -> JSONResponse:
        body = ErrorOut(type="invalid_token", message=str(exc))
        return JSONResponse(status_code=401, content=body.model_dump())

    @app.exception_handler(InsufficientScopeError)
    async def _insufficient_scope(_: Request, exc: InsufficientScopeError) -> JSONResponse:
        body = ErrorOut(type="insufficient_scope", message=str(exc))
        return JSONResponse(status_code=403, content=body.model_dump())

    @app.exception_handler(ApiKeyNotFoundError)
    async def _api_key_not_found(_: Request, exc: ApiKeyNotFoundError) -> JSONResponse:
        body = ErrorOut(type="api_key_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(AuthDomainError)
    async def _domain_error(_: Request, exc: AuthDomainError) -> JSONResponse:
        body = ErrorOut(type="auth_domain_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
