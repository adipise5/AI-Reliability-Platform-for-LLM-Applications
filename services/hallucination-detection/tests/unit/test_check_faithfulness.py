from __future__ import annotations

from uuid import uuid4

from hallucination_detection.application.check_faithfulness import CheckFaithfulnessUseCase
from hallucination_detection.domain.entities import Verdict
from tests.unit.conftest import FakeClaimExtractor, FakeClaimVerifier, FakeFaithfulnessCheckRepository


async def test_execute_persists_a_check_with_all_claims_supported(org_id):
    extractor = FakeClaimExtractor(["claim one", "claim two"])
    verifier = FakeClaimVerifier(Verdict.SUPPORTED)
    repo = FakeFaithfulnessCheckRepository()
    use_case = CheckFaithfulnessUseCase(extractor, verifier, repo)

    check = await use_case.execute(
        org_id=org_id, credential="tok", model="claude-sonnet-5", response="a response", context="the context"
    )

    assert repo.checks[check.id] is check
    assert check.faithfulness_score == 1.0
    assert len(check.claims) == 2
    assert {c.text for c in check.claims} == {"claim one", "claim two"}
    assert extractor.calls == ["a response"]
    assert sorted(verifier.calls) == ["claim one", "claim two"]


async def test_execute_scores_partial_support():
    class VaryingVerifier:
        async def verify(self, credential, *, model, claim, context):
            verdict = Verdict.SUPPORTED if claim == "true claim" else Verdict.CONTRADICTED
            return verdict, None

    extractor = FakeClaimExtractor(["true claim", "false claim"])
    use_case = CheckFaithfulnessUseCase(extractor, VaryingVerifier(), FakeFaithfulnessCheckRepository())

    check = await use_case.execute(
        org_id=uuid4(),
        credential="tok",
        model="m",
        response="r",
        context="c",
    )

    assert check.faithfulness_score == 0.5


async def test_execute_handles_no_extractable_claims(org_id):
    extractor = FakeClaimExtractor([])
    verifier = FakeClaimVerifier()
    use_case = CheckFaithfulnessUseCase(extractor, verifier, FakeFaithfulnessCheckRepository())

    check = await use_case.execute(
        org_id=org_id, credential="tok", model="m", response="hi there!", context="c"
    )

    assert check.claims == ()
    assert check.faithfulness_score == 1.0
    assert verifier.calls == []


async def test_execute_not_enough_info_counts_against_the_score(org_id):
    extractor = FakeClaimExtractor(["a claim"])
    verifier = FakeClaimVerifier(Verdict.NOT_ENOUGH_INFO)
    use_case = CheckFaithfulnessUseCase(extractor, verifier, FakeFaithfulnessCheckRepository())

    check = await use_case.execute(org_id=org_id, credential="tok", model="m", response="r", context="c")

    assert check.faithfulness_score == 0.0
