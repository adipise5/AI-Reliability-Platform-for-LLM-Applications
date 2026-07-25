from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from prompt_registry.application.get_version import GetVersionUseCase
from prompt_registry.domain.entities import PromptVersion
from prompt_registry.domain.errors import PromptNotFoundError, PromptVersionNotFoundError
from tests.unit.conftest import FakePromptRepository, FakePromptVersionRepository


async def test_execute_returns_the_exact_version_requested(org_id, sample_prompt):
    version = PromptVersion(
        id=uuid4(), prompt_id=sample_prompt.id, template="hi", created_at=datetime.now(UTC)
    )
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    version_repo = FakePromptVersionRepository(seed=[version])
    use_case = GetVersionUseCase(prompt_repo, version_repo)

    result = await use_case.execute(org_id=org_id, prompt_id=sample_prompt.id, version_id=version.id)

    assert result == version


async def test_execute_rejects_unknown_prompt(org_id):
    use_case = GetVersionUseCase(FakePromptRepository(), FakePromptVersionRepository())

    with pytest.raises(PromptNotFoundError):
        await use_case.execute(org_id=org_id, prompt_id=uuid4(), version_id=uuid4())


async def test_execute_rejects_a_version_from_a_different_prompt(org_id, sample_prompt):
    stray_version = PromptVersion(id=uuid4(), prompt_id=uuid4(), template="hi", created_at=datetime.now(UTC))
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    version_repo = FakePromptVersionRepository(seed=[stray_version])
    use_case = GetVersionUseCase(prompt_repo, version_repo)

    with pytest.raises(PromptVersionNotFoundError):
        await use_case.execute(org_id=org_id, prompt_id=sample_prompt.id, version_id=stray_version.id)
