"""HTTP client for GitHub's REST API — implements `GitHubClient`.

Authenticates with a single static token (PAT or GitHub App installation
token) from config — see `infrastructure/config.py`'s docstring for the
multi-tenant limitation this implies.
"""

from __future__ import annotations

import httpx

from github_integration.domain.entities import CheckConclusion, CheckStatus
from github_integration.domain.errors import UpstreamServiceError

_API_VERSION = "2022-11-28"


class HttpGitHubClient:
    def __init__(self, base_url: str, *, token: str, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": _API_VERSION,
        }

    async def create_check_run(self, *, repo: str, commit_sha: str, name: str) -> int:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/repos/{repo}/check-runs",
                    json={"name": name, "head_sha": commit_sha, "status": "queued"},
                    headers=self._headers(),
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("github", str(exc)) from exc

        if response.status_code != 201:
            raise UpstreamServiceError("github", f"create check run returned {response.status_code}")
        return int(response.json()["id"])

    async def update_check_run(
        self,
        *,
        repo: str,
        check_run_id: int,
        status: CheckStatus,
        conclusion: CheckConclusion | None,
        summary: str,
    ) -> None:
        payload: dict[str, object] = {
            "status": status.value,
            "output": {"title": "AI Reliability Gate", "summary": summary},
        }
        if conclusion is not None:
            payload["conclusion"] = conclusion.value

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.patch(
                    f"{self._base_url}/repos/{repo}/check-runs/{check_run_id}",
                    json=payload,
                    headers=self._headers(),
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("github", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError("github", f"update check run returned {response.status_code}")

    async def create_pr_comment(self, *, repo: str, pr_number: int, body: str) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/repos/{repo}/issues/{pr_number}/comments",
                    json={"body": body},
                    headers=self._headers(),
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("github", str(exc)) from exc

        if response.status_code != 201:
            raise UpstreamServiceError("github", f"create PR comment returned {response.status_code}")
