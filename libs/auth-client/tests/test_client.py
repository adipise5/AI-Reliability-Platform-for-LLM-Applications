from __future__ import annotations

import httpx
import pytest
import respx

from auth_client.client import AuthServiceClient
from auth_client.errors import AuthServiceUnavailableError, UnauthenticatedError

BASE_URL = "http://auth.internal"


@respx.mock
async def test_introspect_returns_result_on_success():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(
        return_value=httpx.Response(
            200, json={"subject": "user:123", "org_id": "org:1", "scopes": ["chat:write"]}
        )
    )
    client = AuthServiceClient(BASE_URL)

    result = await client.introspect("some-token")

    assert result.subject == "user:123"
    assert result.org_id == "org:1"
    assert result.has_scope("chat:write")


@respx.mock
async def test_introspect_raises_unauthenticated_on_401():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(return_value=httpx.Response(401))
    client = AuthServiceClient(BASE_URL)

    with pytest.raises(UnauthenticatedError):
        await client.introspect("bad-token")


@respx.mock
async def test_introspect_raises_unavailable_on_5xx():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(return_value=httpx.Response(503))
    client = AuthServiceClient(BASE_URL)

    with pytest.raises(AuthServiceUnavailableError):
        await client.introspect("some-token")


@respx.mock
async def test_introspect_raises_unavailable_on_connection_error():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(side_effect=httpx.ConnectError("refused"))
    client = AuthServiceClient(BASE_URL)

    with pytest.raises(AuthServiceUnavailableError):
        await client.introspect("some-token")
