# Dataset Management

Week 4 service. Golden datasets for evaluation: create a dataset, bulk
import items, and read them back — either the current set or any past
import. Authenticates against the real Authentication Service the same
way Prompt Registry does (via `libs/auth-client`'s `RequirePrincipal`),
and every resource is scoped to the caller's `org_id`.

## Layering

```
src/dataset_management/
├── domain/           Dataset, DatasetItem, NewDatasetItem, ImportResult, errors, ports
├── application/      CreateDatasetUseCase, ImportItemsUseCase, GetDatasetUseCase, ListItemsUseCase
├── infrastructure/   SQLAlchemy models/repositories, config
└── api/              FastAPI app, routers, schemas, DI wiring
```

## Versioning model

A dataset's `current_version` starts at `0` ("nothing imported yet") and
advances by one on every bulk import. Items are immutable once imported —
re-importing creates a new version snapshot rather than mutating the
previous one, so an Evaluation Engine run that pinned a version keeps
seeing exactly the fixtures it originally ran against. There's no
separate "export" endpoint: `GET .../items?version=N` returning JSON *is*
the export — building a second code path to do the same read would just
be the same query wearing a different name.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/datasets` | bearer | Create a dataset |
| `POST /api/v1/datasets/{id}/items:bulk` | bearer | Import a batch of items as a new version |
| `GET /api/v1/datasets/{id}` | bearer | Dataset metadata, including `current_version` |
| `GET /api/v1/datasets/{id}/items?version=` | bearer | List items (defaults to the current version) |

## Running locally

```bash
cd services/dataset-management
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn dataset_management.api.main:app --reload --port 8003
```

## Tests

```bash
pytest
```

Same three-layer split as Prompt Registry: `tests/unit/` (fakes),
`tests/integration/test_datasets_api.py` (FastAPI end-to-end, dependencies
overridden), `tests/integration/test_repositories.py` (real SQLAlchemy
repositories against SQLite).

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`):

```bash
docker build -f Dockerfile -t arp-dataset-management ../..
```

Or via `infra/docker-compose.yml`.
