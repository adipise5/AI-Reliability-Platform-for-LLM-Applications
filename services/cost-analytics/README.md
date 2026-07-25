# Cost & Token Analytics

Week 9 service. Every Gateway chat call now emits a usage event here (see
ADR-0006); this service prices it, ledgers it per org, and exposes usage
rollups and a simple monthly budget check.

## Layering

```
src/cost_analytics/
├── domain/           UsageRecord, Budget, PricingRate, UsageSummary, BudgetStatus, ports
├── application/      IngestUsageEventUseCase, GetUsageSummaryUseCase, SetBudgetUseCase,
│                     GetBudgetStatusUseCase
├── infrastructure/    StaticPricingTable, SQLAlchemy repositories, config
└── api/               FastAPI app, routers, schemas, DI wiring
```

## Auth is asymmetric on purpose

- **`POST /api/v1/usage-events` is open** — the Gateway calls it, not a
  user, and pricing every call shouldn't add an auth round trip to every
  chat request. Same "trusted internal network" reasoning as the Trace
  Collector's ingestion endpoint (ADR-0004).
- **Everything else requires a bearer token and is org-scoped.** Unlike
  the Trace Collector, this service tracks real per-tenant financial data
  from day one — that's worth protecting even at this stage, which is why
  this service (not the Trace Collector) is where read-side auth shows up
  first.

## Pricing

`StaticPricingTable` (`infrastructure/pricing.py`) is an in-code lookup,
provider → model → `PricingRate`, with a `"*"` wildcard entry per provider
for "any model I don't have a specific rate for." **The dollar figures in
it are illustrative placeholders, not verified current provider
pricing** — wire it to your actual contracted rates before trusting any
cost figure this service produces for anything real. Ollama's $0.00 is
the one real fact in the table: a locally-run model has no per-token API
fee. A model with no rate at all (`get_rate` returns `None`) is priced at
$0 rather than rejected — an unpriced model shouldn't block usage
tracking for every priced one.

## Budgets

One budget per org (`PUT /api/v1/budget` upserts it). `GET /api/v1/budget`
returns this calendar month's spend against it — `over_budget=true` once
spend exceeds the limit. No alerting is wired yet; that's the
Notification Service's job (Week 12) once it exists.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/usage-events` | none | Record a priced usage event |
| `GET /api/v1/usage` | bearer | This org's usage, rolled up by provider/model |
| `PUT /api/v1/budget` | bearer | Set (or replace) this org's monthly budget |
| `GET /api/v1/budget` | bearer | This month's spend vs. budget |

## Running locally

```bash
cd services/cost-analytics
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn cost_analytics.api.main:app --reload --port 8008
```

## Tests

```bash
pytest
```

`tests/unit/` (fakes for every port), `tests/integration/test_usage_api.py`
and `test_budget_api.py` (FastAPI end-to-end), `tests/integration/test_repositories.py`
(real SQLAlchemy repositories against SQLite).

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). See `infra/docker-compose.yml`.
