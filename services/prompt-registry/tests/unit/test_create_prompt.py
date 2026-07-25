from __future__ import annotations

import pytest

from prompt_registry.application.create_prompt import CreatePromptUseCase
from prompt_registry.domain.errors import DuplicatePromptNameError
from tests.unit.conftest import FakePromptRepository


async def test_execute_creates_a_prompt_scoped_to_the_org(org_id):
    repo = FakePromptRepository()
    use_case = CreatePromptUseCase(repo)

    prompt = await use_case.execute(org_id=org_id, name="support-agent")

    assert repo.prompts[prompt.id] is prompt
    assert prompt.org_id == org_id
    assert prompt.name == "support-agent"


async def test_execute_rejects_duplicate_name_within_the_same_org(org_id, sample_prompt):
    repo = FakePromptRepository(seed=[sample_prompt])
    use_case = CreatePromptUseCase(repo)

    with pytest.raises(DuplicatePromptNameError):
        await use_case.execute(org_id=org_id, name=sample_prompt.name)


async def test_execute_allows_the_same_name_in_a_different_org(sample_prompt):
    from uuid import uuid4

    repo = FakePromptRepository(seed=[sample_prompt])
    use_case = CreatePromptUseCase(repo)

    prompt = await use_case.execute(org_id=uuid4(), name=sample_prompt.name)

    assert prompt.name == sample_prompt.name
    assert prompt.org_id != sample_prompt.org_id
