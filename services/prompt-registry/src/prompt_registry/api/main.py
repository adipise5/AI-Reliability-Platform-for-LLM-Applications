from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from prompt_registry.api.routers import health, prompts
from prompt_registry.api.schemas import ErrorOut
from prompt_registry.domain.errors import (
    DuplicatePromptNameError,
    NoActiveVersionError,
    PromptNotFoundError,
    PromptRegistryError,
    PromptVersionNotFoundError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Prompt Registry",
        version="0.1.0",
        description="Versioned prompt templates, diffing, and environment promotion.",
    )

    # Standard request-count/latency histograms at GET /metrics — see
    # docs/deployment.md's Grafana section for the dashboard that reads them.
    Instrumentator().instrument(app).expose(app)

    app.include_router(health.router)
    app.include_router(prompts.router)

    @app.exception_handler(DuplicatePromptNameError)
    async def _duplicate_name(_: Request, exc: DuplicatePromptNameError) -> JSONResponse:
        body = ErrorOut(type="duplicate_prompt_name", message=str(exc))
        return JSONResponse(status_code=409, content=body.model_dump())

    @app.exception_handler(PromptNotFoundError)
    async def _prompt_not_found(_: Request, exc: PromptNotFoundError) -> JSONResponse:
        body = ErrorOut(type="prompt_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(PromptVersionNotFoundError)
    async def _version_not_found(_: Request, exc: PromptVersionNotFoundError) -> JSONResponse:
        body = ErrorOut(type="prompt_version_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(NoActiveVersionError)
    async def _no_active_version(_: Request, exc: NoActiveVersionError) -> JSONResponse:
        body = ErrorOut(type="no_active_version", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(PromptRegistryError)
    async def _domain_error(_: Request, exc: PromptRegistryError) -> JSONResponse:
        body = ErrorOut(type="prompt_registry_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
