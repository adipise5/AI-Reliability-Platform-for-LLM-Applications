from __future__ import annotations

from uuid import uuid4

import pytest

from prompt_registry.application.create_version import CreateVersionUseCase
from prompt_registry.domain.errors import PromptNotFoundError
from tests.unit.conftest import FakePromptRepository, FakePromptVersionRepository


async def test_execute_creates_a_version_for_an_owned_prompt(org_id, sample_prompt):
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    version_repo = FakePromptVersionRepository()
    use_case = CreateVersionUseCase(prompt_repo, version_repo)

    version = await use_case.execute(
        org_id=org_id,
        prompt_id=sample_prompt.id,
        template="You are a helpful {{role}}.",
        variables_schema={"role": "string"},
        semver_tag="v1",
    )

    assert version_repo.versions[version.id] is version
    assert version.prompt_id == sample_prompt.id
    assert version.variables_schema == {"role": "string"}


async def test_execute_rejects_unknown_prompt(org_id):
    use_case = CreateVersionUseCase(FakePromptRepository(), FakePromptVersionRepository())

    with pytest.raises(PromptNotFoundError):
        await use_case.execute(org_id=org_id, prompt_id=uuid4(), template="hi")


async def test_execute_rejects_a_prompt_owned_by_another_org(sample_prompt):
    prompt_repo = FakePromptRepository(seed=[sample_prompt])
    use_case = CreateVersionUseCase(prompt_repo, FakePromptVersionRepository())

    with pytest.raises(PromptNotFoundError):
        await use_case.execute(org_id=uuid4(), prompt_id=sample_prompt.id, template="hi")
