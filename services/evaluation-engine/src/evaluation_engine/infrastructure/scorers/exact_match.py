"""The one deterministic scorer this "core" milestone ships with —
string equality after whitespace trimming. Good enough for golden-answer
datasets (math, classification, extraction); free-form generation needs
`llm_judge` instead.
"""

from __future__ import annotations

from evaluation_engine.domain.entities import Score


class ExactMatchScorer:
    name = "exact_match"

    async def score(
        self, *, credential: str, output: str, expected_output: object, context: dict[str, object]
    ) -> Score:
        matched = str(output).strip() == str(expected_output).strip()
        return Score(
            scorer_name=self.name,
            value=1.0 if matched else 0.0,
            evidence={"expected": expected_output, "actual": output},
        )
