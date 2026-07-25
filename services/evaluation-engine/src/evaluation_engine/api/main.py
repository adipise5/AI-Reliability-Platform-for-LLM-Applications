from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from evaluation_engine.api.routers import health, runs
from evaluation_engine.api.schemas import ErrorOut
from evaluation_engine.domain.errors import (
    EvalRunNotFoundError,
    EvaluationEngineError,
    PromptRenderError,
    UnknownScorerError,
    UpstreamServiceError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Evaluation Engine",
        version="0.1.0",
        description="Runs prompt versions against datasets, scores the results, and tracks run status.",
    )

    app.include_router(health.router)
    app.include_router(runs.router)

    @app.exception_handler(EvalRunNotFoundError)
    async def _not_found(_: Request, exc: EvalRunNotFoundError) -> JSONResponse:
        body = ErrorOut(type="eval_run_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(UnknownScorerError)
    async def _unknown_scorer(_: Request, exc: UnknownScorerError) -> JSONResponse:
        body = ErrorOut(type="unknown_scorer", message=str(exc))
        return JSONResponse(status_code=400, content=body.model_dump())

    @app.exception_handler(UpstreamServiceError)
    async def _upstream_error(_: Request, exc: UpstreamServiceError) -> JSONResponse:
        body = ErrorOut(type="upstream_service_error", message=str(exc))
        return JSONResponse(status_code=502, content=body.model_dump())

    @app.exception_handler(PromptRenderError)
    async def _render_error(_: Request, exc: PromptRenderError) -> JSONResponse:
        body = ErrorOut(type="prompt_render_error", message=str(exc))
        return JSONResponse(status_code=400, content=body.model_dump())

    @app.exception_handler(EvaluationEngineError)
    async def _domain_error(_: Request, exc: EvaluationEngineError) -> JSONResponse:
        body = ErrorOut(type="evaluation_engine_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
