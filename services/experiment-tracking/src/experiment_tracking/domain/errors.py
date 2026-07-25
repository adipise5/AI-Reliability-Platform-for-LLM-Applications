from __future__ import annotations

from uuid import UUID


class ExperimentTrackingError(Exception):
    """Base class for all domain errors raised by Experiment Tracking."""


class ExperimentNotFoundError(ExperimentTrackingError):
    def __init__(self, experiment_id: UUID) -> None:
        self.experiment_id = experiment_id
        super().__init__(f"no experiment {experiment_id} in this org")


class DuplicateExperimentNameError(ExperimentTrackingError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"an experiment named {name!r} already exists in this org")


class RunNotFoundError(ExperimentTrackingError):
    def __init__(self, run_id: UUID) -> None:
        self.run_id = run_id
        super().__init__(f"no eval run {run_id} visible to this credential")


class UpstreamServiceError(ExperimentTrackingError):
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        super().__init__(f"[{service}] {message}")
