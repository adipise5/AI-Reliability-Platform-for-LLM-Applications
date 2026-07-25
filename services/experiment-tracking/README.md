# Experiment Tracking

Week 8 service. Cross-run comparison and score history — deliberately
**not** a second store of run results. See
[ADR-0005](../../docs/architecture/decisions/0005-evaluation-engine-owns-results-and-forwards-credentials.md):
the Evaluation Engine owns `eval_runs`/`run_item_results` directly; this
service is a thin aggregation layer that groups run ids into named
experiments and fetches the real data fresh from the Evaluation Engine on
every read.

## What this service owns (and doesn't)

- **Owns:** `Experiment` — an org-scoped, named grouping of eval run ids
  (`experiment_tracking.experiments`, `run_ids` embedded as JSON — a
  small, append-mostly list with no independent lifecycle).
- **Doesn't own:** anything about the runs themselves. Comparing an
  experiment or fetching score history means calling the Evaluation
  Engine's `GET /api/v1/runs/{id}` and `GET /api/v1/runs?prompt_id=`
  fresh, every time — `GetScoreHistoryUseCase` is a pure passthrough with
  no local storage involved at all.

Adding a run to an experiment confirms it's real first — a call to the
Evaluation Engine (`AddRunUseCase`) — so an experiment never accumulates
run ids that don't resolve to anything.

## Layering

```
src/experiment_tracking/
├── domain/           Experiment, RemoteEvalRunSummary, errors, ports
├── application/      CreateExperimentUseCase, AddRunUseCase, CompareExperimentUseCase,
│                     GetScoreHistoryUseCase, GetExperimentUseCase
├── infrastructure/    HttpEvalRunReader (the Evaluation Engine client), SQLAlchemy
│                      repository, config
└── api/               FastAPI app, routers, schemas, DI wiring
```

## Auth

Same credential-forwarding pattern as the Evaluation Engine (ADR-0005):
the caller's bearer token authenticates the request here *and* is
forwarded to the Evaluation Engine, since that's what determines which
org's runs are visible. Same JWT-TTL caveat applies.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/experiments` | bearer | Create a named experiment |
| `POST /api/v1/experiments/{id}/runs` | bearer | Attach an eval run (validated against the Evaluation Engine) |
| `GET /api/v1/experiments/{id}` | bearer | Experiment metadata + its run ids |
| `GET /api/v1/experiments/{id}/comparison` | bearer | Every linked run's current data, fetched live |
| `GET /api/v1/score-history?prompt_id=` | bearer | Every run for a prompt, most recent first |

## Running locally

```bash
cd services/experiment-tracking
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn experiment_tracking.api.main:app --reload --port 8007
```

## Tests

```bash
pytest
```

- `tests/unit/` — every use case against fakes for the repository and the
  Evaluation Engine reader; `HttpEvalRunReader`'s 404-vs-other-error
  mapping tested directly with respx.
- `tests/integration/test_experiments_api.py` — the FastAPI app
  end-to-end.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repository against SQLite.

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). See `infra/docker-compose.yml`.
