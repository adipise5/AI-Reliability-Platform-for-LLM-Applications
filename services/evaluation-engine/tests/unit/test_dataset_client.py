from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from evaluation_engine.domain.errors import UpstreamServiceError
from evaluation_engine.infrastructure.clients.dataset_client import HttpDatasetClient

BASE_URL = "http://dataset-mgmt.internal"


@respx.mock
async def test_get_items_uses_the_explicit_version_without_resolving_current():
    dataset_id = uuid4()
    route = respx.get(f"{BASE_URL}/api/v1/datasets/{dataset_id}/items").mock(
        return_value=httpx.Response(200, json=[])
    )
    client = HttpDatasetClient(BASE_URL)

    version, items = await client.get_items("tok", dataset_id=dataset_id, version=3)

    assert version == 3
    assert items == []
    assert route.calls.last.request.url.params["version"] == "3"


@respx.mock
async def test_get_items_resolves_current_version_when_none_given():
    dataset_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/datasets/{dataset_id}").mock(
        return_value=httpx.Response(200, json={"id": str(dataset_id), "current_version": 5})
    )
    item_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/datasets/{dataset_id}/items").mock(
        return_value=httpx.Response(
            200, json=[{"id": str(item_id), "input": {"q": "x"}, "expected_output": "y"}]
        )
    )
    client = HttpDatasetClient(BASE_URL)

    version, items = await client.get_items("tok", dataset_id=dataset_id, version=None)

    assert version == 5
    assert items[0].id == item_id
    assert items[0].expected_output == "y"


@respx.mock
async def test_get_items_raises_on_upstream_error():
    dataset_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/datasets/{dataset_id}/items").mock(
        return_value=httpx.Response(500, json={"type": "x", "message": "boom"})
    )
    client = HttpDatasetClient(BASE_URL)

    with pytest.raises(UpstreamServiceError):
        await client.get_items("tok", dataset_id=dataset_id, version=1)
