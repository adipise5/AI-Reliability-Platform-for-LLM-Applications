"""Covers the ADR-0003 adapter-selection rule in api/deps.py: static keys
win when configured (dev/test convenience), otherwise the gateway talks to
the real Authentication Service."""

from __future__ import annotations

from gateway.api import deps
from gateway.infrastructure.auth.remote_auth_adapter import RemoteAuthServiceAdapter
from gateway.infrastructure.auth.static_key_auth import StaticAPIKeyAuthAdapter


def test_static_keys_take_priority_when_configured(monkeypatch):
    monkeypatch.setenv("GATEWAY_STATIC_API_KEYS", "dev-key")
    deps.reset_cached_singletons()

    adapter = deps._build_auth_adapter()

    assert isinstance(adapter, StaticAPIKeyAuthAdapter)
    deps.reset_cached_singletons()


def test_falls_back_to_remote_auth_service_when_no_static_keys(monkeypatch):
    monkeypatch.setenv("GATEWAY_STATIC_API_KEYS", "")
    monkeypatch.setenv("GATEWAY_AUTH_SERVICE_URL", "http://auth.internal")
    deps.reset_cached_singletons()

    adapter = deps._build_auth_adapter()

    assert isinstance(adapter, RemoteAuthServiceAdapter)
    deps.reset_cached_singletons()
