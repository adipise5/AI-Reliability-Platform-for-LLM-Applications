from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from prompt_registry.application.get_active_version import GetActiveVersionUseCase
from prompt_registry.domain.entities import PromotionEvent, PromptVersion
from prompt_registry.domain.errors import NoActiveVersionError, PromptNotFoundError
from tests.unit.conftest import FakePromotionRepository, FakePromptRepository, FakePromptVersionRepository


def _make_version(prompt_id) -> PromptVersion:
    return PromptVersion(id=uuid4(), prompt_id=prompt_id, template="hi", created_at=datetime.now(UTC))


def _make_event(prompt_id, version_id, environment, *, when) -> PromotionEvent:
    return PromotionEvent(
        id=uuid4(), prompt_id=prompt_id, version_id=version_id, environment=environment, created_at=when
    )


async def test_execute_returns_the_most_recently_promoted_version(org_id, sample_prompt):
    older_version = _make_version(sample_prompt.id)
    newer_version = _make_version(sample_prompt.id)
    now = datetime.now(UTC)
    events = [
        _make_event(sample_prompt.id, older_version.id, "prod", when=now - timedelta(hours=1)),
        _make_event(sample_prompt.id, newer_version.id, "prod", when=now),
    ]
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    version_repo = FakePromptVersionRepository(seed=[older_version, newer_version])
    promotion_repo = FakePromotionRepository(seed=events)
    use_case = GetActiveVersionUseCase(prompt_repo, version_repo, promotion_repo)

    active = await use_case.execute(org_id=org_id, prompt_id=sample_prompt.id, environment="prod")

    assert active.id == newer_version.id


async def test_execute_raises_when_nothing_promoted_to_that_environment(org_id, sample_prompt):
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    use_case = GetActiveVersionUseCase(
        prompt_repo, FakePromptVersionRepository(), FakePromotionRepository()
    )

    with pytest.raises(NoActiveVersionError):
        await use_case.execute(org_id=org_id, prompt_id=sample_prompt.id, environment="staging")


async def test_execute_rejects_unknown_prompt(org_id):
    use_case = GetActiveVersionUseCase(
        FakePromptRepository(), FakePromptVersionRepository(), FakePromotionRepository()
    )

    with pytest.raises(PromptNotFoundError):
        await use_case.execute(org_id=org_id, prompt_id=uuid4(), environment="prod")
