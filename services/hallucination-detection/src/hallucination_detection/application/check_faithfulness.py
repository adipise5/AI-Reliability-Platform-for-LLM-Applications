"""Use case: extract claims from a response, verify each against the
supplied context, and record the result.

Verification runs concurrently across claims (`asyncio.gather`) — each is
an independent Gateway call, and a response with a dozen claims
shouldn't take a dozen sequential round trips.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from hallucination_detection.domain.entities import Claim, FaithfulnessCheck
from hallucination_detection.domain.ports import ClaimExtractor, ClaimVerifier, FaithfulnessCheckRepository


class CheckFaithfulnessUseCase:
    def __init__(
        self,
        extractor: ClaimExtractor,
        verifier: ClaimVerifier,
        repo: FaithfulnessCheckRepository,
    ) -> None:
        self._extractor = extractor
        self._verifier = verifier
        self._repo = repo

    async def execute(
        self, *, org_id: UUID, credential: str, model: str, response: str, context: str
    ) -> FaithfulnessCheck:
        claim_texts = await self._extractor.extract(credential, model=model, response=response)

        claims: list[Claim] = []
        if claim_texts:
            verified = await asyncio.gather(
                *(
                    self._verify_one(credential, model=model, claim_text=text, context=context)
                    for text in claim_texts
                )
            )
            claims.extend(verified)

        check = FaithfulnessCheck(
            id=uuid4(),
            org_id=org_id,
            response=response,
            context=context,
            claims=tuple(claims),
            created_at=datetime.now(UTC),
        )
        await self._repo.create(check)
        return check

    async def _verify_one(self, credential: str, *, model: str, claim_text: str, context: str) -> Claim:
        verdict, evidence = await self._verifier.verify(
            credential, model=model, claim=claim_text, context=context
        )
        return Claim(text=claim_text, verdict=verdict, evidence=evidence)
