"""Shared error-mapping helper for the three upstream HTTP clients."""

from __future__ import annotations

import httpx

from evaluation_engine.domain.errors import UpstreamServiceError


def raise_for_upstream_status(response: httpx.Response, *, service: str) -> None:
    if response.status_code >= 400:
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text
        raise UpstreamServiceError(service, f"{response.status_code}: {detail}")
