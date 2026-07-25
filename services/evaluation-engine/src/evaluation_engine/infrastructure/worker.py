"""The Celery worker process: defines the app and the one task that
actually executes an eval run.

Each task invocation builds and disposes its own `AsyncEngine` rather than
reusing a cached one (contrast with every other service's `api/deps.py`,
which caches the engine for the process's lifetime). `asyncio.run()`
creates a fresh event loop per call and a SQLAlchemy async engine's
connection pool is bound to the loop it was created on — a cached engine
would break on the second task a worker process picks up. Run this with:

    celery -A evaluation_engine.infrastructure.worker worker -Q q.evaluation
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from celery import Celery

from evaluation_engine.application.execute_run import ExecuteEvalRunUseCase
from evaluation_engine.infrastructure.clients.dataset_client import HttpDatasetClient
from evaluation_engine.infrastructure.clients.gateway_client import HttpGatewayClient
from evaluation_engine.infrastructure.clients.hallucination_client import HttpHallucinationDetectionClient
from evaluation_engine.infrastructure.clients.prompt_registry_client import HttpPromptRegistryClient
from evaluation_engine.infrastructure.config import get_settings
from evaluation_engine.infrastructure.db import build_engine, build_session_factory
from evaluation_engine.infrastructure.repositories import (
    SqlAlchemyEvalRunRepository,
    SqlAlchemyRunItemResultRepository,
)
from evaluation_engine.infrastructure.scorers.exact_match import ExactMatchScorer
from evaluation_engine.infrastructure.scorers.faithfulness import FaithfulnessScorer
from evaluation_engine.infrastructure.scorers.llm_judge import LLMJudgeScorer
from evaluation_engine.infrastructure.scorers.registry import InMemoryScorerRegistry

_startup_settings = get_settings()
app = Celery("evaluation_engine", broker=_startup_settings.redis_url, backend=_startup_settings.redis_url)
app.conf.task_default_queue = "q.evaluation"


@app.task(name="evaluation_engine.execute_run")  # type: ignore[untyped-decorator]
def execute_run_task(run_id: str, credential: str) -> None:
    asyncio.run(_execute(run_id, credential))


async def _execute(run_id: str, credential: str) -> None:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    try:
        session_factory = build_session_factory(engine)
        async with session_factory() as session:
            gateway = HttpGatewayClient(settings.gateway_url, timeout=settings.upstream_timeout_seconds)
            use_case = ExecuteEvalRunUseCase(
                eval_run_repo=SqlAlchemyEvalRunRepository(session),
                item_repo=SqlAlchemyRunItemResultRepository(session),
                prompt_registry=HttpPromptRegistryClient(
                    settings.prompt_registry_url, timeout=settings.upstream_timeout_seconds
                ),
                dataset_client=HttpDatasetClient(
                    settings.dataset_mgmt_url, timeout=settings.upstream_timeout_seconds
                ),
                gateway=gateway,
                scorer_registry=InMemoryScorerRegistry(
                    [
                        ExactMatchScorer(),
                        LLMJudgeScorer(gateway, judge_model=settings.judge_model),
                        FaithfulnessScorer(
                            HttpHallucinationDetectionClient(
                                settings.hallucination_service_url,
                                timeout=settings.upstream_timeout_seconds,
                            ),
                            judge_model=settings.judge_model,
                        ),
                    ]
                ),
            )
            await use_case.execute(UUID(run_id), credential)
    finally:
        await engine.dispose()
