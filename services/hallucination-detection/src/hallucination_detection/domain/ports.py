from __future__ import annotations

from typing import Protocol
from uuid import UUID

from hallucination_detection.domain.entities import FaithfulnessCheck, Verdict


class ClaimExtractor(Protocol):
    async def extract(self, credential: str, *, model: str, response: str) -> list[str]:
        """Splits `response` into atomic factual claims. An empty list
        means "nothing to verify" (e.g. a purely conversational reply),
        not a failure."""
        ...


class ClaimVerifier(Protocol):
    async def verify(
        self, credential: str, *, model: str, claim: str, context: str
    ) -> tuple[Verdict, str | None]:
        """Returns `(verdict, evidence)` — `evidence` is a short
        justification string, or `None` if the model didn't give one."""
        ...


class FaithfulnessCheckRepository(Protocol):
    async def create(self, check: FaithfulnessCheck) -> None: ...

    async def get_by_id(self, check_id: UUID) -> FaithfulnessCheck | None: ...
