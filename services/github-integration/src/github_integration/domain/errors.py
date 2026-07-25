from __future__ import annotations

from uuid import UUID


class GitHubIntegrationError(Exception):
    """Base class for all domain errors raised by this service."""


class InvalidWebhookSignatureError(GitHubIntegrationError):
    def __init__(self) -> None:
        super().__init__("webhook signature missing or invalid")


class CheckNotFoundError(GitHubIntegrationError):
    def __init__(self, check_id: UUID) -> None:
        self.check_id = check_id
        super().__init__(f"no check {check_id} in this org")


class CheckAlreadyCompletedError(GitHubIntegrationError):
    def __init__(self, check_id: UUID) -> None:
        self.check_id = check_id
        super().__init__(f"check {check_id} is already completed")


class UpstreamServiceError(GitHubIntegrationError):
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        super().__init__(f"[{service}] {message}")
