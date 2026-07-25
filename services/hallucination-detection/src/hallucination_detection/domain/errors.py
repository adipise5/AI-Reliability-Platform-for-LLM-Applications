from __future__ import annotations

from uuid import UUID


class HallucinationDetectionError(Exception):
    """Base class for all domain errors raised by this service."""


class FaithfulnessCheckNotFoundError(HallucinationDetectionError):
    def __init__(self, check_id: UUID) -> None:
        self.check_id = check_id
        super().__init__(f"no faithfulness check {check_id} in this org")


class UpstreamServiceError(HallucinationDetectionError):
    """The Gateway rejected or failed to service a claim-extraction or
    claim-verification request."""

    def __init__(self, message: str) -> None:
        super().__init__(f"[gateway] {message}")
