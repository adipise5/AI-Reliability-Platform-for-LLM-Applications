from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from prompt_registry.application.diff_versions import DiffVersionsUseCase
from prompt_registry.domain.entities import PromptVersion
from prompt_registry.domain.errors import PromptNotFoundError, PromptVersionNotFoundError
from tests.unit.conftest import FakePromptRepository, FakePromptVersionRepository


def _make_version(prompt_id, template: str) -> PromptVersion:
    return PromptVersion(
        id=uuid4(), prompt_id=prompt_id, template=template, created_at=datetime.now(UTC)
    )


async def test_execute_returns_a_unified_diff_between_two_versions(org_id, sample_prompt):
    version_a = _make_version(sample_prompt.id, "line one\nline two")
    version_b = _make_version(sample_prompt.id, "line one\nline three")
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    version_repo = FakePromptVersionRepository(seed=[version_a, version_b])
    use_case = DiffVersionsUseCase(prompt_repo, version_repo)

    diff = await use_case.execute(
        org_id=org_id, prompt_id=sample_prompt.id, version_a_id=version_a.id, version_b_id=version_b.id
    )

    joined = "\n".join(diff.unified_diff)
    assert "-line two" in joined
    assert "+line three" in joined


async def test_execute_rejects_a_version_not_on_the_prompt(org_id, sample_prompt):
    version_a = _make_version(sample_prompt.id, "hi")
    stray_version = _make_version(uuid4(), "hi")
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    version_repo = FakePromptVersionRepository(seed=[version_a, stray_version])
    use_case = DiffVersionsUseCase(prompt_repo, version_repo)

    with pytest.raises(PromptVersionNotFoundError):
        await use_case.execute(
            org_id=org_id,
            prompt_id=sample_prompt.id,
            version_a_id=version_a.id,
            version_b_id=stray_version.id,
        )


async def test_execute_rejects_unknown_prompt(org_id):
    use_case = DiffVersionsUseCase(FakePromptRepository(), FakePromptVersionRepository())

    with pytest.raises(PromptNotFoundError):
        await use_case.execute(
            org_id=org_id, prompt_id=uuid4(), version_a_id=uuid4(), version_b_id=uuid4()
        )
