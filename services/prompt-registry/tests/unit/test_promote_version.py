from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from prompt_registry.application.promote_version import PromoteVersionUseCase
from prompt_registry.domain.entities import PromptVersion
from prompt_registry.domain.errors import PromptNotFoundError, PromptVersionNotFoundError
from tests.unit.conftest import FakePromotionRepository, FakePromptRepository, FakePromptVersionRepository


def _make_version(prompt_id) -> PromptVersion:
    return PromptVersion(id=uuid4(), prompt_id=prompt_id, template="hi", created_at=datetime.now(UTC))


async def test_execute_promotes_a_version_belonging_to_the_prompt(org_id, sample_prompt):
    version = _make_version(sample_prompt.id)
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    version_repo = FakePromptVersionRepository(seed=[version])
    promotion_repo = FakePromotionRepository()
    use_case = PromoteVersionUseCase(prompt_repo, version_repo, promotion_repo)

    event = await use_case.execute(
        org_id=org_id, prompt_id=sample_prompt.id, version_id=version.id, environment="prod"
    )

    assert promotion_repo.events == [event]
    assert event.version_id == version.id
    assert event.environment == "prod"


async def test_execute_rejects_unknown_prompt(org_id):
    use_case = PromoteVersionUseCase(
        FakePromptRepository(), FakePromptVersionRepository(), FakePromotionRepository()
    )

    with pytest.raises(PromptNotFoundError):
        await use_case.execute(org_id=org_id, prompt_id=uuid4(), version_id=uuid4(), environment="prod")


async def test_execute_rejects_a_version_from_a_different_prompt(org_id, sample_prompt):
    other_prompt_id = uuid4()
    version_of_other_prompt = _make_version(other_prompt_id)
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    version_repo = FakePromptVersionRepository(seed=[version_of_other_prompt])
    use_case = PromoteVersionUseCase(prompt_repo, version_repo, FakePromotionRepository())

    with pytest.raises(PromptVersionNotFoundError):
        await use_case.execute(
            org_id=org_id,
            prompt_id=sample_prompt.id,
            version_id=version_of_other_prompt.id,
            environment="prod",
        )
