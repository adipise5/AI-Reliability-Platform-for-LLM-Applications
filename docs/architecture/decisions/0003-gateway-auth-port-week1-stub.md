# ADR-0003: Gateway authenticates through a port, stubbed with static keys until Week 2

## Status
Accepted — 2026-07-19. Updated 2026-07-19 (Week 2): see "Week 2 update" below —
the static adapter was kept rather than removed.

## Context
The Gateway is Week 1's deliverable; the Authentication Service (orgs, users,
JWT, RBAC) is Week 2's. The Gateway must still reject unauthenticated
requests from day one — an open LLM proxy is not a shippable Week 1
increment — but it cannot yet call a service that doesn't exist.

## Decision
Define an `AuthPort` in `services/gateway/src/gateway/domain/ports.py` with a
single method, `authenticate(credential: str) -> AuthContext`. Week 1 ships
`StaticAPIKeyAuthAdapter` in `infrastructure/auth/`, which validates a
request's bearer token against a set of keys read from configuration
(`GATEWAY_STATIC_API_KEYS`, comma-separated). Week 2 adds
`RemoteAuthServiceAdapter`, which instead calls the Authentication Service's
`POST /api/v1/auth/introspect` and is swapped in via dependency wiring in
`api/deps.py` — no change to `domain/`, `application/`, or any route
handler.

## Consequences
- The Gateway is usable and access-controlled in Week 1 without a hard
  dependency on an unbuilt service.
- The swap to real multi-tenant auth in Week 2 is confined to one new
  adapter file and one line in `api/deps.py`.
- Static keys are a deliberate, temporary reduction in scope: no per-org
  scoping, rate limits, or key rotation until `RemoteAuthServiceAdapter`
  lands. This is documented in the Gateway's own `README.md` so it is not
  mistaken for the final auth model.

## Week 2 update
`RemoteAuthServiceAdapter` landed in `infrastructure/auth/remote_auth_adapter.py`,
built on the new shared `libs/auth-client` package rather than a bespoke
HTTP call, so every future service authenticates against the Authentication
Service the same way. The original plan was a hard swap; in practice
`api/deps.py`'s `_build_auth_adapter()` keeps both adapters and selects one
by configuration: `StaticAPIKeyAuthAdapter` wins when
`GATEWAY_STATIC_API_KEYS` is set, otherwise `RemoteAuthServiceAdapter` is
used. This isn't scope creep — it's the port/adapter pattern's own
selection mechanism, formalized — and it means running the Gateway alone
(no Postgres, no Auth Service) for a quick local check is still one
env var away, without that convenience leaking into how the adapters
themselves are written.

A new domain error, `AuthServiceUnavailableError`, was added alongside
`AuthenticationError`: an unreachable Authentication Service is a `503`,
not a `401` — the credential itself may be perfectly valid.
