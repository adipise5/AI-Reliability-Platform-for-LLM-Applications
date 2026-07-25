from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from github_integration.api.routers import checks, health, webhooks
from github_integration.api.schemas import ErrorOut
from github_integration.domain.errors import (
    CheckAlreadyCompletedError,
    CheckNotFoundError,
    GitHubIntegrationError,
    InvalidWebhookSignatureError,
    UpstreamServiceError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="GitHub Integration",
        version="0.1.0",
        description="Webhooks, check runs, and PR comments — the CI-facing surface of the platform.",
    )

    # Standard request-count/latency histograms at GET /metrics — see
    # docs/deployment.md's Grafana section for the dashboard that reads them.
    Instrumentator().instrument(app).expose(app)

    app.include_router(health.router)
    app.include_router(webhooks.router)
    app.include_router(checks.router)

    @app.exception_handler(InvalidWebhookSignatureError)
    async def _invalid_signature(_: Request, exc: InvalidWebhookSignatureError) -> JSONResponse:
        body = ErrorOut(type="invalid_webhook_signature", message=str(exc))
        return JSONResponse(status_code=401, content=body.model_dump())

    @app.exception_handler(CheckNotFoundError)
    async def _check_not_found(_: Request, exc: CheckNotFoundError) -> JSONResponse:
        body = ErrorOut(type="check_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(CheckAlreadyCompletedError)
    async def _check_already_completed(_: Request, exc: CheckAlreadyCompletedError) -> JSONResponse:
        body = ErrorOut(type="check_already_completed", message=str(exc))
        return JSONResponse(status_code=409, content=body.model_dump())

    @app.exception_handler(UpstreamServiceError)
    async def _upstream_error(_: Request, exc: UpstreamServiceError) -> JSONResponse:
        body = ErrorOut(type="upstream_service_error", message=str(exc))
        return JSONResponse(status_code=502, content=body.model_dump())

    @app.exception_handler(GitHubIntegrationError)
    async def _domain_error(_: Request, exc: GitHubIntegrationError) -> JSONResponse:
        body = ErrorOut(type="github_integration_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
