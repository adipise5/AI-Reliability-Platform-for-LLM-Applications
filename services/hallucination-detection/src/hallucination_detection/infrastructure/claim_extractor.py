from __future__ import annotations

from hallucination_detection.infrastructure.gateway_client import HttpGatewayClient

_EXTRACTION_PROMPT = (
    "Break the following response into a list of atomic factual claims — "
    "each claim should be a single, independently checkable statement.\n"
    "If the response makes no factual claims (e.g. it's a greeting, an "
    "opinion, or a question), output nothing.\n"
    'Output one claim per line, each starting with "- ", and nothing else '
    "— no preamble, no numbering, no closing remarks.\n\n"
    "Response:\n{response}"
)


class GatewayClaimExtractor:
    def __init__(self, gateway: HttpGatewayClient) -> None:
        self._gateway = gateway

    async def extract(self, credential: str, *, model: str, response: str) -> list[str]:
        prompt = _EXTRACTION_PROMPT.format(response=response)
        raw = await self._gateway.complete(credential, model=model, prompt=prompt)

        claims: list[str] = []
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped.startswith("-"):
                continue
            claim = stripped.lstrip("-").strip()
            if claim:
                claims.append(claim)
        return claims
