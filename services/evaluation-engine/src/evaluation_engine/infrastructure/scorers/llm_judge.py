"""Scores free-form output by asking a judge model to grade it against the
expected answer, via the same `GatewayPort` the run itself used — the
judge is just another Gateway call, routed through whichever provider the
configured `judge_model` maps to.

Judge non-determinism is a real limitation for regression detection (see
docs/architecture/overview.md's risk register): pin the judge model and
use temperature=0 here so at least this scorer's *own* variance is
minimized, even though the judge's underlying quality is still a moving
target across model versions.
"""

from __future__ import annotations

from evaluation_engine.domain.entities import Score
from evaluation_engine.domain.ports import GatewayPort

_JUDGE_PROMPT = (
    "You are grading whether an AI response correctly matches an expected answer.\n"
    "Expected answer: {expected}\n"
    "Actual response: {actual}\n"
    "Respond with ONLY a single number between 0 and 1 indicating how well the "
    "actual response matches the expected answer, where 1 means a perfect match "
    "and 0 means completely wrong. Do not include any other text."
)


class LLMJudgeScorer:
    name = "llm_judge"

    def __init__(self, gateway: GatewayPort, *, judge_model: str) -> None:
        self._gateway = gateway
        self._judge_model = judge_model

    async def score(
        self, *, credential: str, output: str, expected_output: object, context: dict[str, object]
    ) -> Score:
        judge_prompt = _JUDGE_PROMPT.format(expected=expected_output, actual=output)
        completion = await self._gateway.complete(
            credential,
            model=self._judge_model,
            prompt=judge_prompt,
            temperature=0.0,
            max_tokens=10,
        )

        evidence: dict[str, object] = {
            "judge_model": self._judge_model,
            "judge_raw_response": completion.content,
        }
        try:
            value = max(0.0, min(1.0, float(completion.content.strip())))
        except ValueError:
            value = 0.0
            evidence["parse_error"] = True

        return Score(scorer_name=self.name, value=value, evidence=evidence)
