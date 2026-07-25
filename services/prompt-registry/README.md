# Prompt Registry

Week 3 service. Versioned prompt templates: create, diff, and promote to
an environment (`prod`, `staging`, ...). Every version is immutable —
consumers (the Gateway, later the Evaluation Engine) reference a specific
version `id`, never "latest," so eval runs stay reproducible.

This is the first service besides the Gateway to authenticate against the
real Authentication Service, via `libs/auth-client`'s shared
`RequirePrincipal` FastAPI dependency (see that library's `fastapi.py`).
Every resource is scoped to the caller's `org_id` — a prompt from another
org 404s rather than 403s, so its existence isn't leaked.

## Layering

```
src/prompt_registry/
├── domain/           Prompt, PromptVersion, PromotionEvent, VersionDiff, errors, ports
├── application/      CreatePromptUseCase, CreateVersionUseCase, PromoteVersionUseCase,
│                     GetActiveVersionUseCase, DiffVersionsUseCase
├── infrastructure/    SQLAlchemy models/repositories, config
└── api/               FastAPI app, routers, schemas, DI wiring
```

## Model

- **Prompt** — a named container, unique per `(org_id, name)`.
- **PromptVersion** — an immutable template + variables schema snapshot.
- **PromotionEvent** — append-only: "environment X points at version Y as
  of now." The *active* version for an environment is whichever promotion
  happened most recently for that `(prompt_id, environment)` pair — there's
  no separate mutable "current pointer" row to keep in sync.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/prompts` | bearer | Create a prompt |
| `POST /api/v1/prompts/{id}/versions` | bearer | Create an immutable version |
| `POST /api/v1/prompts/{id}/promotions` | bearer | Promote a version to an environment |
| `GET /api/v1/prompts/{id}/versions/active?environment=` | bearer | Resolve the active version |
| `GET /api/v1/prompts/{id}/versions/diff?a=&b=` | bearer | Unified diff between two versions' templates |

Any authenticated principal from the owning org may call these — there's
no dedicated `prompts:write` scope yet (only `chat:write`/`org:admin`
exist so far). Adding finer-grained scopes is an Authentication Service
change, not something this service needs to anticipate today.

## Running locally

Needs PostgreSQL (see `infra/docker-compose.yml`) and the Authentication
Service reachable at `PROMPT_REGISTRY_AUTH_SERVICE_URL`:

```bash
cd services/prompt-registry
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn prompt_registry.api.main:app --reload --port 8002
```

## Tests

```bash
pytest
```

- `tests/unit/` — use cases against in-memory fakes.
- `tests/integration/test_prompts_api.py` — the FastAPI app end-to-end,
  with repositories and `require_principal` overridden — includes a test
  that two different orgs' prompts are invisible to each other.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repositories against SQLite (schema-translated).

## Docker

Build context is the **repo root**, not this directory — this service
depends on `libs/auth-client`:

```bash
docker build -f Dockerfile -t arp-prompt-registry ../..
```

Or via `infra/docker-compose.yml`.
