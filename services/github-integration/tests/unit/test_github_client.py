from __future__ import annotations

import json

import httpx
import pytest
import respx

from github_integration.domain.entities import CheckConclusion, CheckStatus
from github_integration.domain.errors import UpstreamServiceError
from github_integration.infrastructure.clients.github_client import HttpGitHubClient

BASE_URL = "https://api.github.com"


@respx.mock
async def test_create_check_run_returns_the_github_id():
    route = respx.post(f"{BASE_URL}/repos/acme/widgets/check-runs").mock(
        return_value=httpx.Response(201, json={"id": 42})
    )
    client = HttpGitHubClient(BASE_URL, token="tok", timeout=5.0)

    check_run_id = await client.create_check_run(repo="acme/widgets", commit_sha="a" * 40, name="Gate")

    assert check_run_id == 42
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"name": "Gate", "head_sha": "a" * 40, "status": "queued"}
    assert route.calls.last.request.headers["authorization"] == "Bearer tok"


@respx.mock
async def test_create_check_run_raises_on_non_201():
    respx.post(f"{BASE_URL}/repos/acme/widgets/check-runs").mock(return_value=httpx.Response(422))
    client = HttpGitHubClient(BASE_URL, token="tok", timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.create_check_run(repo="acme/widgets", commit_sha="a" * 40, name="Gate")


@respx.mock
async def test_update_check_run_sends_conclusion_and_summary():
    route = respx.patch(f"{BASE_URL}/repos/acme/widgets/check-runs/42").mock(
        return_value=httpx.Response(200)
    )
    client = HttpGitHubClient(BASE_URL, token="tok", timeout=5.0)

    await client.update_check_run(
        repo="acme/widgets",
        check_run_id=42,
        status=CheckStatus.COMPLETED,
        conclusion=CheckConclusion.SUCCESS,
        summary="all good",
    )

    sent = json.loads(route.calls.last.request.content)
    assert sent["status"] == "completed"
    assert sent["conclusion"] == "success"
    assert sent["output"]["summary"] == "all good"


@respx.mock
async def test_update_check_run_raises_on_non_200():
    respx.patch(f"{BASE_URL}/repos/acme/widgets/check-runs/42").mock(return_value=httpx.Response(404))
    client = HttpGitHubClient(BASE_URL, token="tok", timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.update_check_run(
            repo="acme/widgets",
            check_run_id=42,
            status=CheckStatus.COMPLETED,
            conclusion=CheckConclusion.FAILURE,
            summary="bad",
        )


@respx.mock
async def test_create_pr_comment_posts_body():
    route = respx.post(f"{BASE_URL}/repos/acme/widgets/issues/7/comments").mock(
        return_value=httpx.Response(201)
    )
    client = HttpGitHubClient(BASE_URL, token="tok", timeout=5.0)

    await client.create_pr_comment(repo="acme/widgets", pr_number=7, body="hi")

    sent = json.loads(route.calls.last.request.content)
    assert sent == {"body": "hi"}


@respx.mock
async def test_create_pr_comment_raises_on_non_201():
    respx.post(f"{BASE_URL}/repos/acme/widgets/issues/7/comments").mock(return_value=httpx.Response(403))
    client = HttpGitHubClient(BASE_URL, token="tok", timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.create_pr_comment(repo="acme/widgets", pr_number=7, body="hi")
