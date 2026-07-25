from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from experiment_tracking.api.routers import experiments, health, score_history
from experiment_tracking.api.schemas import ErrorOut
from experiment_tracking.domain.errors import (
    DuplicateExperimentNameError,
    ExperimentNotFoundError,
    ExperimentTrackingError,
    RunNotFoundError,
    UpstreamServiceError,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Experiment Tracking",
        version="0.1.0",
        description="Cross-run comparison and score history, aggregated from the Evaluation Engine.",
    )

    app.include_router(health.router)
    app.include_router(experiments.router)
    app.include_router(score_history.router)

    @app.exception_handler(DuplicateExperimentNameError)
    async def _duplicate_name(_: Request, exc: DuplicateExperimentNameError) -> JSONResponse:
        body = ErrorOut(type="duplicate_experiment_name", message=str(exc))
        return JSONResponse(status_code=409, content=body.model_dump())

    @app.exception_handler(ExperimentNotFoundError)
    async def _not_found(_: Request, exc: ExperimentNotFoundError) -> JSONResponse:
        body = ErrorOut(type="experiment_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(RunNotFoundError)
    async def _run_not_found(_: Request, exc: RunNotFoundError) -> JSONResponse:
        body = ErrorOut(type="run_not_found", message=str(exc))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(UpstreamServiceError)
    async def _upstream_error(_: Request, exc: UpstreamServiceError) -> JSONResponse:
        body = ErrorOut(type="upstream_service_error", message=str(exc))
        return JSONResponse(status_code=502, content=body.model_dump())

    @app.exception_handler(ExperimentTrackingError)
    async def _domain_error(_: Request, exc: ExperimentTrackingError) -> JSONResponse:
        body = ErrorOut(type="experiment_tracking_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
