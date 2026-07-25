from __future__ import annotations

from uuid import UUID


class EvaluationEngineError(Exception):
    """Base class for all domain errors raised by the Evaluation Engine."""


class EvalRunNotFoundError(EvaluationEngineError):
    def __init__(self, run_id: UUID) -> None:
        self.run_id = run_id
        super().__init__(f"no eval run {run_id} in this org")


class UnknownScorerError(EvaluationEngineError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"no scorer registered under {name!r}")


class UpstreamServiceError(EvaluationEngineError):
    """Prompt Registry, Dataset Management, or the Gateway rejected or
    failed to service a request this run depends on."""

    def __init__(self, service: str, message: str) -> None:
        self.service = service
        super().__init__(f"[{service}] {message}")


class PromptRenderError(EvaluationEngineError):
    def __init__(self, dataset_item_id: UUID, reason: str) -> None:
        self.dataset_item_id = dataset_item_id
        super().__init__(f"failed to render template for item {dataset_item_id}: {reason}")
