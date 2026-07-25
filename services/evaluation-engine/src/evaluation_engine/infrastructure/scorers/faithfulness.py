"""Scores groundedness by delegating to the Hallucination Detection
service (Week 7) — this is the dependency
`docs/architecture/overview.md`'s service catalog names explicitly
("Evaluation Engine ... Hallucination Detection").

Only usable when a dataset item's `input` carries a `context` field (the
source passage a RAG-style response should be grounded in). Items without
one are scored vacuously faithful — nothing to check groundedness
against — the same convention the Hallucination service itself uses for a
response with no extractable claims.
"""

from __future__ import annotations

from evaluation_engine.domain.entities import Score
from evaluation_engine.domain.ports import HallucinationDetectionPort


class FaithfulnessScorer:
    name = "faithfulness"

    def __init__(self, client: HallucinationDetectionPort, *, judge_model: str) -> None:
        self._client = client
        self._judge_model = judge_model

    async def score(
        self, *, credential: str, output: str, expected_output: object, context: dict[str, object]
    ) -> Score:
        item_input = context.get("item_input")
        source_context = item_input.get("context") if isinstance(item_input, dict) else None

        if not source_context:
            return Score(
                scorer_name=self.name,
                value=1.0,
                evidence={"skipped": "dataset item provided no 'context' field to check against"},
            )

        score_value, claim_count = await self._client.check_faithfulness(
            credential, model=self._judge_model, response=str(output), context=str(source_context)
        )
        return Score(
            scorer_name=self.name,
            value=score_value,
            evidence={"claim_count": claim_count, "judge_model": self._judge_model},
        )
