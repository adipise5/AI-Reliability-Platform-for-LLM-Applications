from __future__ import annotations

from uuid import UUID


class RegressionDetectionError(Exception):
    """Base class for all domain errors raised by this service."""


class RunNotCompletedError(RegressionDetectionError):
    def __init__(self, run_id: UUID) -> None:
        self.run_id = run_id
        super().__init__(f"eval run {run_id} has no completed score to gate yet")


class GateDecisionNotFoundError(RegressionDetectionError):
    def __init__(self, run_id: UUID) -> None:
        self.run_id = run_id
        super().__init__(f"no gate decision recorded for run {run_id}")


class BaselineNotFoundError(RegressionDetectionError):
    def __init__(self, prompt_id: UUID) -> None:
        self.prompt_id = prompt_id
        super().__init__(f"no baseline recorded for prompt {prompt_id} yet")


class UpstreamServiceError(RegressionDetectionError):
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        super().__init__(f"[{service}] {message}")
