from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from dashboard_backend.domain.errors import UpstreamServiceError
from dashboard_backend.infrastructure.clients.github_integration_client import HttpGitHubChecksReader

BASE_URL = "http://github-integration.internal"


@respx.mock
async def test_list_checks_sends_repo_and_commit_sha_filters():
    route = respx.get(f"{BASE_URL}/api/v1/checks").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": str(uuid4()),
                    "org_id": str(uuid4()),
                    "repo": "acme/widgets",
                    "commit_sha": "a" * 40,
                    "github_check_run_id": 123,
                    "status": "completed",
                    "conclusion": "success",
                    "run_id": str(uuid4()),
                    "created_at": "2026-01-01T00:00:00Z",
                    "completed_at": "2026-01-01T00:01:00Z",
                }
            ],
        )
    )
    client = HttpGitHubChecksReader(BASE_URL, timeout=5.0)

    checks = await client.list_checks("tok", repo="acme/widgets", commit_sha="a" * 40)

    assert len(checks) == 1
    assert route.calls.last.request.url.params["repo"] == "acme/widgets"
    assert route.calls.last.request.url.params["commit_sha"] == "a" * 40


@respx.mock
async def test_list_checks_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/checks").mock(return_value=httpx.Response(500))
    client = HttpGitHubChecksReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.list_checks("tok")
