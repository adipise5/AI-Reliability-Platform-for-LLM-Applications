from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from auth.application.introspect import IntrospectUseCase
from auth.domain.entities import ApiKey
from auth.domain.errors import InvalidTokenError
from tests.unit.conftest import FakeApiKeyRepository, FakeApiKeySecretHasher, FakeTokenIssuer


async def test_execute_resolves_a_session_token(sample_owner):
    issuer = FakeTokenIssuer()
    token = issuer.issue(sample_owner)
    use_case = IntrospectUseCase(issuer, FakeApiKeyRepository(), FakeApiKeySecretHasher())

    principal = await use_case.execute(token)

    assert principal.org_id == sample_owner.org_id
    assert principal.scopes == sample_owner.scopes


async def test_execute_resolves_an_active_api_key():
    hasher = FakeApiKeySecretHasher()
    org_id = uuid4()
    secret = "arp_live_deadbeef.some-random-secret"
    key = ApiKey(
        id=uuid4(),
        org_id=org_id,
        name="k",
        prefix="arp_live_deadbeef",
        secret_hash=hasher.hash(secret),
        scopes=frozenset({"chat:write"}),
        created_at=datetime.now(UTC),
    )
    use_case = IntrospectUseCase(FakeTokenIssuer(), FakeApiKeyRepository(seed=[key]), hasher)

    principal = await use_case.execute(secret)

    assert principal.subject == f"api_key:{key.id}"
    assert principal.org_id == org_id
    assert principal.scopes == frozenset({"chat:write"})


async def test_execute_rejects_a_revoked_api_key():
    hasher = FakeApiKeySecretHasher()
    secret = "arp_live_deadbeef.some-random-secret"
    key = ApiKey(
        id=uuid4(),
        org_id=uuid4(),
        name="k",
        prefix="arp_live_deadbeef",
        secret_hash=hasher.hash(secret),
        scopes=frozenset({"chat:write"}),
        created_at=datetime.now(UTC),
        revoked_at=datetime.now(UTC),
    )
    use_case = IntrospectUseCase(FakeTokenIssuer(), FakeApiKeyRepository(seed=[key]), hasher)

    with pytest.raises(InvalidTokenError):
        await use_case.execute(secret)


async def test_execute_rejects_garbage_credentials():
    use_case = IntrospectUseCase(FakeTokenIssuer(), FakeApiKeyRepository(), FakeApiKeySecretHasher())

    with pytest.raises(InvalidTokenError):
        await use_case.execute("not-a-token-or-key")
