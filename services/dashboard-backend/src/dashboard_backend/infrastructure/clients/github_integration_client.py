"""HTTP client for GitHub Integration — implements `GitHubChecksReader`
by forwarding the caller's own bearer credential."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from dashboard_backend.domain.entities import RemoteCheckRun
from dashboard_backend.domain.errors import UpstreamServiceError


class HttpGitHubChecksReader:
    def __init__(self, base_url: str, *, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def list_checks(
        self, credential: str, *, repo: str | None = None, commit_sha: str | None = None
    ) -> list[RemoteCheckRun]:
        params: dict[str, str] = {}
        if repo is not None:
            params["repo"] = repo
        if commit_sha is not None:
            params["commit_sha"] = commit_sha

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/api/v1/checks",
                    params=params,
                    headers={"Authorization": f"Bearer {credential}"},
                )
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("github-integration", str(exc)) from exc

        if response.status_code != 200:
            raise UpstreamServiceError(
                "github-integration", f"GET /checks returned {response.status_code}"
            )
        return [_parse_check(item) for item in response.json()]


def _parse_check(payload: dict[str, Any]) -> RemoteCheckRun:
    return RemoteCheckRun(
        id=UUID(str(payload["id"])),
        repo=str(payload["repo"]),
        commit_sha=str(payload["commit_sha"]),
        status=str(payload["status"]),
        conclusion=payload["conclusion"],
        run_id=UUID(str(payload["run_id"])) if payload.get("run_id") is not None else None,
    )
