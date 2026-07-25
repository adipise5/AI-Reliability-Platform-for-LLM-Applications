"""Use case: mint a new API key for an org.

The full secret is only ever returned here, at creation time — from then on
only its hash is stored (see infrastructure/security). Losing it means
generating a new key.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from uuid import UUID, uuid4

from auth.domain.entities import ApiKey
from auth.domain.errors import InsufficientScopeError
from auth.domain.ports import ApiKeyRepository, ApiKeySecretHasher

# "." never appears in secrets.token_hex/token_urlsafe output, so it's an
# unambiguous separator between the (lookup-able) prefix and the secret —
# see IntrospectUseCase, which splits on it to find which row to check.
_SEPARATOR = "."


class CreateApiKeyUseCase:
    def __init__(
        self,
        api_key_repo: ApiKeyRepository,
        secret_hasher: ApiKeySecretHasher,
        *,
        key_environment: str = "live",
    ) -> None:
        self._api_key_repo = api_key_repo
        self._secret_hasher = secret_hasher
        self._key_environment = key_environment

    async def execute(
        self,
        *,
        org_id: UUID,
        name: str,
        creator_scopes: frozenset[str],
        requested_scopes: frozenset[str] | None = None,
    ) -> tuple[ApiKey, str]:
        scopes = creator_scopes if requested_scopes is None else requested_scopes
        if not scopes.issubset(creator_scopes):
            raise InsufficientScopeError(scopes, creator_scopes)

        prefix = f"arp_{self._key_environment}_{secrets.token_hex(4)}"
        full_secret = f"{prefix}{_SEPARATOR}{secrets.token_urlsafe(32)}"

        api_key = ApiKey(
            id=uuid4(),
            org_id=org_id,
            name=name,
            prefix=prefix,
            secret_hash=self._secret_hasher.hash(full_secret),
            scopes=scopes,
            created_at=datetime.now(UTC),
        )
        await self._api_key_repo.create(api_key)
        return api_key, full_secret
