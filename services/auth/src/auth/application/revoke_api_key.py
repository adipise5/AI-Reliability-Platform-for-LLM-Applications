"""Use case: revoke an API key, scoped to the org that owns it."""

from __future__ import annotations

from uuid import UUID

from auth.domain.errors import ApiKeyNotFoundError
from auth.domain.ports import ApiKeyRepository


class RevokeApiKeyUseCase:
    def __init__(self, api_key_repo: ApiKeyRepository) -> None:
        self._api_key_repo = api_key_repo

    async def execute(self, *, org_id: UUID, key_id: UUID) -> None:
        api_key = await self._api_key_repo.get_by_id(key_id)
        if api_key is None or api_key.org_id != org_id:
            # An org can't tell the difference between "no such key" and
            # "that key belongs to someone else" — both are 404s upstream.
            raise ApiKeyNotFoundError(str(key_id))
        await self._api_key_repo.revoke(key_id)
