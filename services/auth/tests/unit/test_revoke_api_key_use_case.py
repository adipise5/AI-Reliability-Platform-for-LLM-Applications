from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from auth.application.revoke_api_key import RevokeApiKeyUseCase
from auth.domain.entities import ApiKey
from auth.domain.errors import ApiKeyNotFoundError
from tests.unit.conftest import FakeApiKeyRepository


def _make_key(org_id) -> ApiKey:
    return ApiKey(
        id=uuid4(),
        org_id=org_id,
        name="k",
        prefix="arp_live_deadbeef",
        secret_hash="hash",
        scopes=frozenset({"chat:write"}),
        created_at=datetime.now(UTC),
    )


async def test_execute_revokes_a_key_belonging_to_the_org():
    org_id = uuid4()
    key = _make_key(org_id)
    repo = FakeApiKeyRepository(seed=[key])
    use_case = RevokeApiKeyUseCase(repo)

    await use_case.execute(org_id=org_id, key_id=key.id)

    assert repo.keys[key.id].revoked_at is not None


async def test_execute_rejects_a_key_belonging_to_another_org():
    key = _make_key(org_id=uuid4())
    repo = FakeApiKeyRepository(seed=[key])
    use_case = RevokeApiKeyUseCase(repo)

    with pytest.raises(ApiKeyNotFoundError):
        await use_case.execute(org_id=uuid4(), key_id=key.id)


async def test_execute_rejects_unknown_key_id():
    use_case = RevokeApiKeyUseCase(FakeApiKeyRepository())

    with pytest.raises(ApiKeyNotFoundError):
        await use_case.execute(org_id=uuid4(), key_id=uuid4())
