from __future__ import annotations

import pytest

from gateway.domain.errors import AuthenticationError
from gateway.infrastructure.auth.static_key_auth import StaticAPIKeyAuthAdapter


async def test_authenticate_accepts_a_configured_key():
    adapter = StaticAPIKeyAuthAdapter(frozenset({"dev-local-key"}))

    context = await adapter.authenticate("dev-local-key")

    assert context.has_scope("chat:write")
    assert context.org_id == "static-dev-org"


@pytest.mark.parametrize("credential", ["", "wrong-key"])
async def test_authenticate_rejects_missing_or_unknown_keys(credential):
    adapter = StaticAPIKeyAuthAdapter(frozenset({"dev-local-key"}))

    with pytest.raises(AuthenticationError):
        await adapter.authenticate(credential)
