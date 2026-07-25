from __future__ import annotations

from uuid import uuid4

import pytest

from auth.application.create_api_key import CreateApiKeyUseCase
from auth.domain.errors import InsufficientScopeError
from tests.unit.conftest import FakeApiKeyRepository, FakeApiKeySecretHasher


async def test_execute_defaults_to_creator_scopes():
    repo = FakeApiKeyRepository()
    use_case = CreateApiKeyUseCase(repo, FakeApiKeySecretHasher(), key_environment="test")
    org_id = uuid4()

    api_key, secret = await use_case.execute(
        org_id=org_id, name="ci key", creator_scopes=frozenset({"chat:write", "org:admin"})
    )

    assert repo.keys[api_key.id] is api_key
    assert api_key.scopes == frozenset({"chat:write", "org:admin"})
    assert secret.startswith(api_key.prefix + ".")
    assert api_key.prefix.startswith("arp_test_")
    assert api_key.is_active


async def test_execute_honors_narrower_requested_scopes():
    use_case = CreateApiKeyUseCase(FakeApiKeyRepository(), FakeApiKeySecretHasher())

    api_key, _ = await use_case.execute(
        org_id=uuid4(),
        name="read only",
        creator_scopes=frozenset({"chat:write", "org:admin"}),
        requested_scopes=frozenset({"chat:write"}),
    )

    assert api_key.scopes == frozenset({"chat:write"})


async def test_execute_rejects_scopes_the_creator_does_not_have():
    use_case = CreateApiKeyUseCase(FakeApiKeyRepository(), FakeApiKeySecretHasher())

    with pytest.raises(InsufficientScopeError):
        await use_case.execute(
            org_id=uuid4(),
            name="escalation attempt",
            creator_scopes=frozenset({"chat:write"}),
            requested_scopes=frozenset({"chat:write", "org:admin"}),
        )


async def test_stored_hash_verifies_the_returned_secret():
    hasher = FakeApiKeySecretHasher()
    use_case = CreateApiKeyUseCase(FakeApiKeyRepository(), hasher)

    api_key, secret = await use_case.execute(
        org_id=uuid4(), name="k", creator_scopes=frozenset({"chat:write"})
    )

    assert hasher.verify(secret, api_key.secret_hash)
