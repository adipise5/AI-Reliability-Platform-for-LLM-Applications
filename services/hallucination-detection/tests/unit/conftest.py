from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from hallucination_detection.domain.entities import FaithfulnessCheck, Verdict


class FakeClaimExtractor:
    def __init__(self, claims: list[str] | None = None) -> None:
        self._claims = claims if claims is not None else ["the sky is blue"]
        self.calls: list[str] = []

    async def extract(self, credential: str, *, model: str, response: str) -> list[str]:
        self.calls.append(response)
        return self._claims


class FakeClaimVerifier:
    def __init__(self, verdict: Verdict = Verdict.SUPPORTED, evidence: str | None = "because") -> None:
        self._verdict = verdict
        self._evidence = evidence
        self.calls: list[str] = []

    async def verify(
        self, credential: str, *, model: str, claim: str, context: str
    ) -> tuple[Verdict, str | None]:
        self.calls.append(claim)
        return self._verdict, self._evidence


class FakeFaithfulnessCheckRepository:
    def __init__(self, seed: list[FaithfulnessCheck] | None = None) -> None:
        self.checks: dict[UUID, FaithfulnessCheck] = {c.id: c for c in (seed or [])}

    async def create(self, check: FaithfulnessCheck) -> None:
        self.checks[check.id] = check

    async def get_by_id(self, check_id: UUID) -> FaithfulnessCheck | None:
        return self.checks.get(check_id)


@pytest.fixture
def org_id() -> UUID:
    return uuid4()
