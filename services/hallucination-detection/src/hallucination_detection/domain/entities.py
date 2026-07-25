"""Domain entities for Hallucination / Faithfulness Detection — see
ADR-0001: no framework imports here.

The technique: extract the candidate response into atomic factual claims,
then check each claim against the supplied context independently — the
same claim-extraction-then-NLI-verification shape used by RAG-faithfulness
evaluators like RAGAS's faithfulness metric, not a novel invention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Verdict(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    NOT_ENOUGH_INFO = "not_enough_info"


@dataclass(frozen=True, slots=True)
class Claim:
    text: str
    verdict: Verdict
    evidence: str | None = None


@dataclass(frozen=True, slots=True)
class FaithfulnessCheck:
    """`faithfulness_score` is the fraction of claims marked `SUPPORTED` —
    `NOT_ENOUGH_INFO` counts against the score the same as
    `CONTRADICTED`, deliberately: "the context doesn't confirm this" is
    not the same as "this is grounded," and treating it as a wash would
    understate ungrounded responses that merely sound plausible.
    """

    id: UUID
    org_id: UUID
    response: str
    context: str
    claims: tuple[Claim, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def faithfulness_score(self) -> float:
        if not self.claims:
            return 1.0  # nothing asserted, nothing to contradict
        supported = sum(1 for c in self.claims if c.verdict == Verdict.SUPPORTED)
        return supported / len(self.claims)
