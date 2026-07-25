# Authentication Service

Week 2 service. Orgs, users, API keys, JWT sessions, and RBAC for the
whole platform — every other service authenticates by calling this one's
introspection endpoint (via `libs/auth-client`), rather than validating
credentials itself. See
[`docs/architecture/overview.md`](../../docs/architecture/overview.md) and
[ADR-0003](../../docs/architecture/decisions/0003-gateway-auth-port-week1-stub.md)
for how the Gateway consumes this.

## Layering

```
src/auth/
├── domain/           entities (Org, User, ApiKey, Principal), RBAC scopes, errors, ports
├── application/      RegisterOrgUseCase, LoginUseCase, CreateApiKeyUseCase,
│                     RevokeApiKeyUseCase, IntrospectUseCase
├── infrastructure/   SQLAlchemy models/repositories, bcrypt password hasher,
│                     sha256 api-key hasher, JWT issuer, config
└── api/              FastAPI app, routers, request/response schemas, DI wiring
```

Same rules as the Gateway (ADR-0001): `domain/` and `application/` never
import FastAPI, SQLAlchemy, or a crypto library directly — those are
`infrastructure/` adapters behind ports.

## RBAC model

Three fixed roles, each with a fixed scope set (`domain/entities.py`):

| Role | Scopes |
|---|---|
| `owner` / `admin` | `chat:write`, `org:admin` |
| `member` | `chat:write` |

An API key's scopes default to its creator's scopes, or a caller-chosen
subset — a key can never carry more scope than the user who minted it
(`InsufficientScopeError`, 403).

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/orgs` | none | Register a new org + owner user |
| `POST /api/v1/auth/login` | none | Email + password → JWT |
| `POST /api/v1/auth/introspect` | none* | Resolve any bearer credential → subject/org/scopes |
| `POST /api/v1/api-keys` | JWT, `org:admin` | Mint an API key |
| `DELETE /api/v1/api-keys/{id}` | JWT, `org:admin` | Revoke an API key |

\* Introspection takes the credential as a request body, not a header — it's
what's *being checked*, not the caller's own credential. Every other
service treats this endpoint as internal (called from the platform
network, via `libs/auth-client`), not a public API.

Credentials are one of:
- **A session JWT**, from `/auth/login` — short-lived (`AUTH_JWT_TTL_SECONDS`), used by the (future) dashboard and for managing API keys.
- **An API key**, from `/api-keys` — long-lived, `arp_<env>_<id>.<secret>` shaped, used by SDKs/CI/the Gateway. The `.` splits a lookup-able prefix from the secret; only a hash of the whole thing is ever stored (see `infrastructure/security/api_key_hasher.py`).

## Running locally

Needs PostgreSQL (see `infra/docker-compose.yml` for a batteries-included
setup, or point `AUTH_DATABASE_URL` at your own instance):

```bash
cd services/auth
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn auth.api.main:app --reload --port 8001
```

```bash
curl -s http://localhost:8001/api/v1/orgs \
  -H "Content-Type: application/json" \
  -d '{"org_name": "Acme", "owner_email": "owner@acme.com", "owner_password": "hunter22222"}'
```

## Tests

```bash
pytest
```

- `tests/unit/` — use cases and the real bcrypt/JWT/sha256 adapters, all
  against fakes or pure inputs; no database.
- `tests/integration/test_*_api.py` — the FastAPI app end-to-end via
  `TestClient`, with repositories overridden by in-memory fakes.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repositories against an in-memory SQLite engine (via a
  `schema_translate_map`, since SQLite has no `auth` schema to translate
  into) — this is what actually exercises the ORM mappings and queries.
  Running these against real Postgres requires `infra/docker-compose.yml`;
  see that test file's docstring for why SQLite is close enough for CI.

## Docker

```bash
docker build -t arp-auth .
docker run -p 8001:8000 --env-file .env arp-auth
```

Or via the repo-wide `infra/docker-compose.yml`, which also starts Postgres
and runs migrations on boot.
