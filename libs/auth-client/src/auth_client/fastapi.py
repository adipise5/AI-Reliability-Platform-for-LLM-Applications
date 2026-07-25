"""Shared FastAPI wiring for services that just need "who is this caller"
and nothing fancier — the RBAC-middleware piece called out in
docs/architecture/overview.md's `libs/` shared-kernel convention.

The Gateway does NOT use this: it supports a static-key dev fallback
alongside remote auth (ADR-0003), which doesn't fit this single-path
shape. This is for services like Prompt Registry and Dataset Management
that always authenticate against the real Authentication Service.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth_client.client import AuthServiceClient
from auth_client.errors import AuthServiceUnavailableError, UnauthenticatedError
from auth_client.models import IntrospectionResult

_bearer_scheme = HTTPBearer(auto_error=False)


class RequirePrincipal:
    """A callable FastAPI dependency bound to one `AuthServiceClient`.

    Construct one per process (typically a module-level `@lru_cache`
    factory in the service's own `api/deps.py`) and use it as
    `Depends(require_principal)`.
    """

    def __init__(self, client: AuthServiceClient) -> None:
        self._client = client

    async def __call__(
        self,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    ) -> IntrospectionResult:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
        try:
            return await self._client.introspect(credentials.credentials)
        except UnauthenticatedError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except AuthServiceUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
            ) from exc
