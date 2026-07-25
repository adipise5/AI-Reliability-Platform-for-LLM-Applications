# Dashboard Backend

Week 14 service. A backend-for-frontend for the React Dashboard (Week
15): the one client the frontend talks to, which fans out to every
other read-facing service on its behalf.

## The one service that owns nothing

Every other service in this project owns a schema and runs Alembic
migrations. This one doesn't — there's no `infrastructure/db.py`, no
`models.py`, no `alembic/` directory at all. It's pure aggregation: a
request comes in with a bearer token, that token gets forwarded to
whichever upstream service(s) the endpoint needs, and the responses get
reshaped into whatever the UI wants. There's nothing here that would
survive a restart, and nothing that needs to.

## What it fans out to

| Port | Upstream service |
|---|---|
| `EvalRunReader` | Evaluation Engine |
| `CostReader` | Cost Analytics |
| `RegressionReader` | Regression Detection |
| `ReportReader` | Report Generator |
| `NotificationReader` | Notification Service |
| `GitHubChecksReader` | GitHub Integration |
| `TraceReader` | Trace Collector |

Every port's credential-forwarding follows the same pattern established
by Experiment Tracking, the Evaluation Engine, and everyone since: the
caller's own bearer token is what determines what they can see upstream,
so it's forwarded, not re-derived.

## A known gap

Prompt Registry, Dataset Management, and Experiment Tracking don't (yet)
expose a "list everything for my org" endpoint — each was built around
narrower access patterns (create, get-by-id, get-active-version,
compare-by-id) that didn't need one at the time. This service therefore
doesn't proxy prompt/dataset/experiment *browsing* — only what's
reachable by an id a caller already has (e.g. an eval run's
`prompt_id`). Adding those list endpoints upstream is a reasonable
follow-up once the React Dashboard's actual navigation needs make clear
what "browse all prompts" should even look like, rather than guessing at
it now.

## The one real aggregation: the dashboard overview

`GET /api/v1/dashboard/overview` is the only endpoint that actually
merges multiple services into one response — recent eval runs, cost
summary, budget status, the Gateway's latency-anomaly check, and recent
notifications, fetched **concurrently** via `asyncio.gather` (same
pattern as the Hallucination Detection service's claim verification).

It's also the one use case in this entire project that's deliberately
tolerant of partial upstream failure: if Cost Analytics doesn't answer,
the overview still returns with `cost_summary: null` rather than failing
the whole request. Every other use case in this codebase is
intentionally fail-fast, because each one represents a single business
transaction (an eval run, a report, a gate decision) that has to stay
correct. A dashboard home page isn't a transaction — it's several
independent reads shown side by side, and a mostly-populated page beats
a blank one. `GET /api/v1/runs/{id}` is the other place two services get
merged (the run plus its regression gate decision, if it has one), but
that one *does* fail normally on a real error, since there's only one
upstream call that matters for identifying the run itself.

## Endpoints

| Method & path | Description |
|---|---|
| `GET /healthz` | Liveness check (no auth) |
| `GET /api/v1/dashboard/overview` | Merged home-page snapshot |
| `GET /api/v1/runs` | Recent eval runs |
| `GET /api/v1/runs/{id}` | A run, its item results, and its gate decision if gated |
| `GET /api/v1/cost/summary` | Token/cost usage summary |
| `GET /api/v1/cost/budget` | Monthly budget status |
| `GET /api/v1/regression/baselines/{prompt_id}` | A prompt's current baseline, if gated at least once |
| `GET /api/v1/regression/latency-anomaly` | Is the Gateway slower than its own recent history? |
| `GET /api/v1/reports?experiment_id=` | Reports, optionally filtered by experiment |
| `GET /api/v1/reports/{id}` | Report metadata |
| `GET /api/v1/notifications/channels` | Configured notification channels |
| `GET /api/v1/notifications?channel_id=` | Sent notifications |
| `GET /api/v1/github/checks?repo=&commit_sha=` | GitHub check runs |
| `GET /api/v1/traces?limit=` | Recent Gateway traces |

Every endpoint except `/healthz` requires a bearer token, including the
ones (like latency-anomaly and traces) whose upstream doesn't — this
BFF is consistently authenticated at its own boundary regardless of what
a given upstream requires.

## Running locally

```bash
cd services/dashboard-backend
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

uvicorn dashboard_backend.api.main:app --reload --port 8013
```

No `alembic upgrade head` step — there's no database.

## Tests

```bash
pytest
```

- `tests/unit/` — every use case against fakes for all seven reader
  ports, including the overview's partial-failure behavior; each HTTP
  client tested directly with respx.
- `tests/integration/` — the FastAPI app end-to-end, per router.

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). See `infra/docker-compose.yml`.
