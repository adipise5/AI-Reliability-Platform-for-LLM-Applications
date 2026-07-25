from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from evaluation_engine.domain.errors import UpstreamServiceError
from evaluation_engine.infrastructure.clients.prompt_registry_client import HttpPromptRegistryClient

BASE_URL = "http://prompt-registry.internal"


@respx.mock
async def test_get_version_returns_the_rendered_version():
    prompt_id, version_id = uuid4(), uuid4()
    respx.get(f"{BASE_URL}/api/v1/prompts/{prompt_id}/versions/{version_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(version_id),
                "prompt_id": str(prompt_id),
                "template": "hi {name}",
                "variables_schema": {},
                "semver_tag": None,
                "created_at": "2026-01-01T00:00:00Z",
            },
        )
    )
    client = HttpPromptRegistryClient(BASE_URL)

    version = await client.get_version("tok", prompt_id=prompt_id, version_id=version_id)

    assert version.template == "hi {name}"
    assert version.id == version_id


@respx.mock
async def test_get_version_raises_on_404():
    prompt_id, version_id = uuid4(), uuid4()
    respx.get(f"{BASE_URL}/api/v1/prompts/{prompt_id}/versions/{version_id}").mock(
        return_value=httpx.Response(404, json={"type": "prompt_version_not_found", "message": "nope"})
    )
    client = HttpPromptRegistryClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.get_version("tok", prompt_id=prompt_id, version_id=version_id)


@respx.mock
async def test_get_version_raises_on_connection_error():
    prompt_id, version_id = uuid4(), uuid4()
    respx.get(f"{BASE_URL}/api/v1/prompts/{prompt_id}/versions/{version_id}").mock(
        side_effect=httpx.ConnectError("refused")
    )
    client = HttpPromptRegistryClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.get_version("tok", prompt_id=prompt_id, version_id=version_id)
