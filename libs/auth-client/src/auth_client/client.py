"""HTTP client for the Authentication Service's introspection endpoint.

Shared by every other service so the request/response shape for
"what does this bearer credential mean" is defined exactly once, per
docs/architecture/overview.md's `libs/` shared-kernel convention.
"""

from __future__ import annotations

import httpx

from auth_client.errors import AuthServiceUnavailableError, UnauthenticatedError
from auth_client.models import IntrospectionResult


class AuthServiceClient:
    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self._http = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def introspect(self, credential: str) -> IntrospectionResult:
        try:
            response = await self._http.post("/api/v1/auth/introspect", json={"credential": credential})
        except httpx.TransportError as exc:
            raise AuthServiceUnavailableError(str(exc)) from exc

        if response.status_code == 401:
            raise UnauthenticatedError("credential rejected by the authentication service")
        if response.status_code >= 500:
            raise AuthServiceUnavailableError(
                f"authentication service returned {response.status_code}"
            )
        response.raise_for_status()

        payload = response.json()
        return IntrospectionResult(
            subject=payload["subject"],
            org_id=payload["org_id"],
            scopes=frozenset(payload["scopes"]),
        )

    async def aclose(self) -> None:
        await self._http.aclose()
