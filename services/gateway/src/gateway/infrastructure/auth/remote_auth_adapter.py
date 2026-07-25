"""Week 2 AuthPort adapter — see ADR-0003.

Delegates to the Authentication Service's `/api/v1/auth/introspect`
endpoint via the shared `auth_client` library, rather than validating
credentials locally. This is the adapter `api/deps.py` selects once
`GATEWAY_AUTH_SERVICE_URL` is the active auth mode (i.e.
`GATEWAY_STATIC_API_KEYS` is unset) — the static-key adapter it replaces
stays in `infrastructure/auth/static_key_auth.py` as a documented dev
fallback.
"""

from __future__ import annotations

from auth_client import AuthServiceClient
from auth_client import AuthServiceUnavailableError as ClientUnavailableError
from auth_client import UnauthenticatedError as ClientUnauthenticatedError

from gateway.domain.entities import AuthContext
from gateway.domain.errors import AuthenticationError, AuthServiceUnavailableError
from gateway.domain.ports import AuthPort


class RemoteAuthServiceAdapter(AuthPort):
    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self._client = AuthServiceClient(base_url, timeout=timeout)

    async def authenticate(self, credential: str) -> AuthContext:
        try:
            result = await self._client.introspect(credential)
        except ClientUnauthenticatedError as exc:
            raise AuthenticationError(str(exc)) from exc
        except ClientUnavailableError as exc:
            raise AuthServiceUnavailableError(str(exc)) from exc

        return AuthContext(subject=result.subject, org_id=result.org_id, scopes=result.scopes)
