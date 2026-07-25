"""Use case: resolve any bearer credential (session JWT or API key) to a
Principal. This is what every other service's auth adapter ultimately
calls through the `/api/v1/auth/introspect` endpoint — see
libs/auth-client and ADR-0003.
"""

from __future__ import annotations

from auth.domain.entities import Principal
from auth.domain.errors import InvalidTokenError
from auth.domain.ports import ApiKeyRepository, ApiKeySecretHasher, TokenIssuer


class IntrospectUseCase:
    def __init__(
        self,
        token_issuer: TokenIssuer,
        api_key_repo: ApiKeyRepository,
        secret_hasher: ApiKeySecretHasher,
    ) -> None:
        self._token_issuer = token_issuer
        self._api_key_repo = api_key_repo
        self._secret_hasher = secret_hasher

    async def execute(self, credential: str) -> Principal:
        try:
            return self._token_issuer.verify(credential)
        except InvalidTokenError:
            pass  # not a session token — fall through and try an API key

        if "." not in credential:
            raise InvalidTokenError("credential is neither a valid session token nor an api key")

        prefix = credential.split(".", 1)[0]
        api_key = await self._api_key_repo.get_by_prefix(prefix)
        if (
            api_key is None
            or not api_key.is_active
            or not self._secret_hasher.verify(credential, api_key.secret_hash)
        ):
            raise InvalidTokenError("unrecognized or revoked api key")

        return Principal(subject=f"api_key:{api_key.id}", org_id=api_key.org_id, scopes=api_key.scopes)
