from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from hallucination_detection.api.routers import checks, health
from hallucination_detection.api.schemas import ErrorOut
from hallucination_detection.domain.errors import (
    FaithfulnessCheckNotFoundError,
    HallucinationDetectionError,
    UpstreamServiceError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hallucination / Faithfulness Detection",
        version="0.1.0",
        description="Claim extraction and context-grounded verification for LLM responses.",
    )

    app.include_router(health.router)
    app.include_router(checks.router)

    @app.exception_handler(FaithfulnessCheckNotFoundError)
    async def _not_found(_: Request, exc: FaithfulnessCheckNotFoundError) -> JSONResponse:
        body = ErrorOut(type="faithfulness_check_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(UpstreamServiceError)
    async def _upstream_error(_: Request, exc: UpstreamServiceError) -> JSONResponse:
        body = ErrorOut(type="upstream_service_error", message=str(exc))
        return JSONResponse(status_code=502, content=body.model_dump())

    @app.exception_handler(HallucinationDetectionError)
    async def _domain_error(_: Request, exc: HallucinationDetectionError) -> JSONResponse:
        body = ErrorOut(type="hallucination_detection_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
