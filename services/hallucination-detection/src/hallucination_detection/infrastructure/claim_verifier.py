from __future__ import annotations

from hallucination_detection.domain.entities import Verdict
from hallucination_detection.infrastructure.gateway_client import HttpGatewayClient

_VERIFICATION_PROMPT = (
    "You are checking whether a claim is supported by the given context.\n\n"
    "Context:\n{context}\n\n"
    "Claim: {claim}\n\n"
    "Respond with the first line being exactly one of: SUPPORTED, "
    "CONTRADICTED, or NOT_ENOUGH_INFO — meaning the context confirms the "
    "claim, the context contradicts the claim, or the context simply "
    "doesn't say either way. On the second line, give a one-sentence "
    "justification."
)


class GatewayClaimVerifier:
    def __init__(self, gateway: HttpGatewayClient) -> None:
        self._gateway = gateway

    async def verify(
        self, credential: str, *, model: str, claim: str, context: str
    ) -> tuple[Verdict, str | None]:
        prompt = _VERIFICATION_PROMPT.format(context=context, claim=claim)
        raw = await self._gateway.complete(credential, model=model, prompt=prompt)

        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        verdict = _parse_verdict(lines[0]) if lines else Verdict.NOT_ENOUGH_INFO
        evidence = lines[1] if len(lines) > 1 else None
        return verdict, evidence


def _parse_verdict(text: str) -> Verdict:
    upper = text.upper()
    if "CONTRADICTED" in upper:
        return Verdict.CONTRADICTED
    if "SUPPORTED" in upper:
        return Verdict.SUPPORTED
    # An unparseable or hedging response is treated the same as "the model
    # said it doesn't know" — never silently counted as faithful.
    return Verdict.NOT_ENOUGH_INFO
