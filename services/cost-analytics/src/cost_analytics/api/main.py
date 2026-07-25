from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from cost_analytics.api.routers import budget, health, usage
from cost_analytics.api.schemas import ErrorOut
from cost_analytics.domain.errors import CostAnalyticsError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cost Analytics",
        version="0.1.0",
        description="Token/cost ledger and per-org budgets for every Gateway call.",
    )

    app.include_router(health.router)
    app.include_router(usage.router)
    app.include_router(budget.router)

    @app.exception_handler(CostAnalyticsError)
    async def _domain_error(_: Request, exc: CostAnalyticsError) -> JSONResponse:
        body = ErrorOut(type="cost_analytics_error", message=str(exc))
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
