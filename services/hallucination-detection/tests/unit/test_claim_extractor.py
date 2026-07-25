from __future__ import annotations

from hallucination_detection.infrastructure.claim_extractor import GatewayClaimExtractor


class _StubGateway:
    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[str] = []

    async def complete(self, credential: str, *, model: str, prompt: str) -> str:
        self.calls.append(prompt)
        return self._content


async def test_extract_parses_bulleted_claims():
    gateway = _StubGateway("- claim one\n- claim two\n")
    extractor = GatewayClaimExtractor(gateway)

    claims = await extractor.extract("tok", model="m", response="some response")

    assert claims == ["claim one", "claim two"]


async def test_extract_ignores_non_bulleted_lines():
    gateway = _StubGateway("Here are the claims:\n- claim one\nThat's all.\n")
    extractor = GatewayClaimExtractor(gateway)

    claims = await extractor.extract("tok", model="m", response="x")

    assert claims == ["claim one"]


async def test_extract_returns_empty_list_when_no_claims():
    gateway = _StubGateway("")
    extractor = GatewayClaimExtractor(gateway)

    claims = await extractor.extract("tok", model="m", response="hi!")

    assert claims == []


async def test_extract_strips_extra_dashes_and_whitespace():
    gateway = _StubGateway("--  claim with extra dashes  \n")
    extractor = GatewayClaimExtractor(gateway)

    claims = await extractor.extract("tok", model="m", response="x")

    assert claims == ["claim with extra dashes"]
