from __future__ import annotations

import httpx
import pytest
import respx

from gateway.domain.errors import AuthenticationError, AuthServiceUnavailableError
from gateway.infrastructure.auth.remote_auth_adapter import RemoteAuthServiceAdapter

BASE_URL = "http://auth.internal"


@respx.mock
async def test_authenticate_returns_auth_context_on_success():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(
        return_value=httpx.Response(
            200, json={"subject": "user:123", "org_id": "org:1", "scopes": ["chat:write"]}
        )
    )
    adapter = RemoteAuthServiceAdapter(BASE_URL)

    context = await adapter.authenticate("some-credential")

    assert context.subject == "user:123"
    assert context.org_id == "org:1"
    assert context.has_scope("chat:write")


@respx.mock
async def test_authenticate_raises_authentication_error_on_rejected_credential():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(return_value=httpx.Response(401))
    adapter = RemoteAuthServiceAdapter(BASE_URL)

    with pytest.raises(AuthenticationError):
        await adapter.authenticate("bad-credential")


@respx.mock
async def test_authenticate_raises_service_unavailable_on_5xx():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(return_value=httpx.Response(503))
    adapter = RemoteAuthServiceAdapter(BASE_URL)

    with pytest.raises(AuthServiceUnavailableError):
        await adapter.authenticate("some-credential")


@respx.mock
async def test_authenticate_raises_service_unavailable_on_connection_error():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(side_effect=httpx.ConnectError("refused"))
    adapter = RemoteAuthServiceAdapter(BASE_URL)

    with pytest.raises(AuthServiceUnavailableError):
        await adapter.authenticate("some-credential")
