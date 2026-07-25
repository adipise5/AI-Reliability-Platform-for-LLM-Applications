"""Use case: actually run an eval — the work the Celery task dispatches
into. Runs synchronously within one task invocation, item by item.

Failure model is deliberately fail-fast for this "core" milestone: any
single item's render or provider failure fails the whole run rather than
recording a partial result and continuing. Partial-run tolerance (score
what succeeded, flag what didn't) is a reasonable follow-up but adds real
complexity — a per-item status, partial aggregate semantics — that isn't
needed to make the engine useful yet.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from evaluation_engine.domain.entities import (
    EvalRun,
    RemoteDatasetItem,
    RemotePromptVersion,
    RunItemResult,
    RunStatus,
    Score,
)
from evaluation_engine.domain.errors import PromptRenderError
from evaluation_engine.domain.ports import (
    DatasetPort,
    EvalRunRepository,
    GatewayPort,
    PromptRegistryPort,
    RunItemResultRepository,
    Scorer,
    ScorerRegistry,
)


class ExecuteEvalRunUseCase:
    def __init__(
        self,
        eval_run_repo: EvalRunRepository,
        item_repo: RunItemResultRepository,
        prompt_registry: PromptRegistryPort,
        dataset_client: DatasetPort,
        gateway: GatewayPort,
        scorer_registry: ScorerRegistry,
    ) -> None:
        self._eval_run_repo = eval_run_repo
        self._item_repo = item_repo
        self._prompt_registry = prompt_registry
        self._dataset_client = dataset_client
        self._gateway = gateway
        self._scorer_registry = scorer_registry

    async def execute(self, run_id: UUID, credential: str) -> None:
        run = await self._eval_run_repo.get_by_id(run_id)
        if run is None:
            return

        run = replace(run, status=RunStatus.RUNNING)
        await self._eval_run_repo.update(run)

        try:
            version = await self._prompt_registry.get_version(
                credential, prompt_id=run.prompt_id, version_id=run.prompt_version_id
            )
            resolved_version, items = await self._dataset_client.get_items(
                credential, dataset_id=run.dataset_id, version=run.dataset_version
            )
            run = replace(run, dataset_version=resolved_version)
            await self._eval_run_repo.update(run)

            scorers = [self._scorer_registry.get(name) for name in run.scorer_names]

            all_scores: list[float] = []
            for item in items:
                result = await self._score_one_item(run, version, item, credential, scorers)
                await self._item_repo.create(result)
                all_scores.extend(score.value for score in result.scores)

            aggregate = sum(all_scores) / len(all_scores) if all_scores else None
            run = replace(
                run,
                status=RunStatus.COMPLETED,
                aggregate_score=aggregate,
                completed_at=datetime.now(UTC),
            )
            await self._eval_run_repo.update(run)
        except Exception as exc:
            failed = replace(
                run, status=RunStatus.FAILED, error_message=str(exc), completed_at=datetime.now(UTC)
            )
            await self._eval_run_repo.update(failed)
            raise

    async def _score_one_item(
        self,
        run: EvalRun,
        version: RemotePromptVersion,
        item: RemoteDatasetItem,
        credential: str,
        scorers: list[Scorer],
    ) -> RunItemResult:
        try:
            rendered = version.template.format(**item.input)
        except (KeyError, IndexError) as exc:
            raise PromptRenderError(item.id, str(exc)) from exc

        completion = await self._gateway.complete(
            credential,
            model=run.model,
            prompt=rendered,
            temperature=run.temperature,
            max_tokens=run.max_tokens,
        )

        scores: list[Score] = []
        for scorer in scorers:
            scores.append(
                await scorer.score(
                    credential=credential,
                    output=completion.content,
                    expected_output=item.expected_output,
                    # `item_input` lets a scorer reach fields the dataset
                    # item carries beyond expected_output — e.g. a
                    # "context" key a RAG-style item supplies for the
                    # `faithfulness` scorer to check groundedness against.
                    context={"model": run.model, "item_input": item.input},
                )
            )

        return RunItemResult(
            id=uuid4(),
            run_id=run.id,
            dataset_item_id=item.id,
            output=completion.content,
            latency_ms=completion.latency_ms,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            scores=tuple(scores),
            created_at=datetime.now(UTC),
        )
