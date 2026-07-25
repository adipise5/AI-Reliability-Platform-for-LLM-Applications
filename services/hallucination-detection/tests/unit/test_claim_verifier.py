from __future__ import annotations

from hallucination_detection.domain.entities import Verdict
from hallucination_detection.infrastructure.claim_verifier import GatewayClaimVerifier


class _StubGateway:
    def __init__(self, content: str) -> None:
        self._content = content

    async def complete(self, credential: str, *, model: str, prompt: str) -> str:
        return self._content


async def test_verify_parses_supported():
    verifier = GatewayClaimVerifier(_StubGateway("SUPPORTED\nThe context says so directly."))

    verdict, evidence = await verifier.verify("tok", model="m", claim="x", context="y")

    assert verdict == Verdict.SUPPORTED
    assert evidence == "The context says so directly."


async def test_verify_parses_contradicted():
    verifier = GatewayClaimVerifier(_StubGateway("CONTRADICTED\nThe context says the opposite."))

    verdict, _ = await verifier.verify("tok", model="m", claim="x", context="y")

    assert verdict == Verdict.CONTRADICTED


async def test_verify_parses_not_enough_info():
    verifier = GatewayClaimVerifier(_StubGateway("NOT_ENOUGH_INFO\nThe context is silent on this."))

    verdict, _ = await verifier.verify("tok", model="m", claim="x", context="y")

    assert verdict == Verdict.NOT_ENOUGH_INFO


async def test_verify_defaults_to_not_enough_info_on_unparseable_response():
    verifier = GatewayClaimVerifier(_StubGateway("I'm not totally sure about this one."))

    verdict, _ = await verifier.verify("tok", model="m", claim="x", context="y")

    assert verdict == Verdict.NOT_ENOUGH_INFO


async def test_verify_returns_none_evidence_when_no_second_line():
    verifier = GatewayClaimVerifier(_StubGateway("SUPPORTED"))

    _, evidence = await verifier.verify("tok", model="m", claim="x", context="y")

    assert evidence is None
