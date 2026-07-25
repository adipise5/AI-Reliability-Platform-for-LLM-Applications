from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from hallucination_detection.domain.entities import Claim, FaithfulnessCheck


class CheckFaithfulnessIn(BaseModel):
    model: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    context: str = Field(..., min_length=1)


class ClaimOut(BaseModel):
    text: str
    verdict: str
    evidence: str | None

    @classmethod
    def from_domain(cls, claim: Claim) -> ClaimOut:
        return cls(text=claim.text, verdict=claim.verdict.value, evidence=claim.evidence)


class FaithfulnessCheckOut(BaseModel):
    id: UUID
    org_id: UUID
    response: str
    context: str
    claims: list[ClaimOut]
    faithfulness_score: float
    created_at: datetime

    @classmethod
    def from_domain(cls, check: FaithfulnessCheck) -> FaithfulnessCheckOut:
        return cls(
            id=check.id,
            org_id=check.org_id,
            response=check.response,
            context=check.context,
            claims=[ClaimOut.from_domain(c) for c in check.claims],
            faithfulness_score=check.faithfulness_score,
            created_at=check.created_at,
        )


class ErrorOut(BaseModel):
    type: str
    message: str
