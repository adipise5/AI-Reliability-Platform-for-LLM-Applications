# Regression Detection Engine

Week 10 service. Two independent features that share nothing but a
name — see the service catalog's original "Baselines, drift, gate
decisions":

1. **Eval-run gating** — is a completed run's score a statistically
   significant drop from this prompt's own history? This is what the
   GitHub Integration (Week 13) will call to fail a CI check.
2. **Latency-anomaly checks** — is the Gateway getting slower right now,
   compared to its own recent history? A stateless read over the Trace
   Collector's trace summaries.

## What this service owns (and doesn't)

- **Owns:** `Baseline` (one row per `org_id`+`prompt_id`, always
  reflecting "every completed run as of the last gate check") and
  `GateDecision` (append-only — every gate check is recorded, so the
  history of *why* a run passed or failed is never overwritten).
- **Doesn't own:** eval run data itself (the Evaluation Engine does, per
  [ADR-0005](../../docs/architecture/decisions/0005-evaluation-engine-owns-results-and-forwards-credentials.md))
  or trace data (the Trace Collector does). Both features fetch fresh
  data from those services on every call rather than caching it.

The baseline is **recomputed from source on every gate check**, not
updated incrementally — every completed run for the prompt is
re-fetched from the Evaluation Engine and re-averaged. This keeps it an
honest, auditable reflection of "the full history as of now," at the
cost of an O(n) fetch per gate check — acceptable at this scale, and
consistent with this project's preference for recomputation over
incremental-update bookkeeping (same call made for Cost Analytics'
budget status in Week 9).

## Verdicts

`EvaluateRunUseCase` computes how many standard deviations below the
prompt's historical mean the observed score is (`(mean - observed) /
stddev`):

- **First completed run for a prompt** — nothing to regress against yet,
  passes by definition, and seeds the baseline.
- `>= fail_threshold_stddev` (default `2.0`) → **fail**
- `>= review_threshold_stddev` (default `1.0`) → **needs_review**
- otherwise → **pass**

If the baseline's stddev is `0` (every prior run scored identically),
the check degrades to a simple `observed >= mean` comparison, since a
z-score against zero variance is undefined.

## Layering

```
src/regression_detection/
├── domain/           Baseline, GateDecision, LatencyAnomalyCheck, errors, ports
├── application/       EvaluateRunUseCase, GetGateDecisionUseCase, GetBaselineUseCase,
│                      CheckLatencyAnomalyUseCase
├── infrastructure/     HttpEvalRunReader, HttpTraceReader, SQLAlchemy repositories, config
└── api/                FastAPI app, routers, schemas, DI wiring
```

## Auth

Gate-decision and baseline endpoints use the same credential-forwarding
pattern as the Evaluation Engine and Experiment Tracking (ADR-0005): the
caller's bearer token authenticates the request here *and* is forwarded
to the Evaluation Engine, since that's what determines which org's runs
are visible. Same JWT-TTL caveat applies.

The latency-anomaly endpoint is deliberately **unauthenticated** — it
reads only from the Trace Collector's own open query API (see
[ADR-0004](../../docs/architecture/decisions/0004-trace-collector-scope-and-span-reconstruction.md)),
which has no org concept yet, so there is nothing to scope the check by.
This asymmetric-auth split mirrors the precedent set by Cost Analytics'
open ingestion endpoint in Week 9.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/gate-decisions` | bearer | Gate a completed eval run against its prompt's baseline |
| `GET /api/v1/gate-decisions/{run_id}` | bearer | Fetch the latest decision recorded for a run |
| `GET /api/v1/baselines/{prompt_id}` | bearer | Current baseline for a prompt |
| `GET /api/v1/latency-anomaly?limit=` | none | Is the Gateway slower right now than its recent history? |

## Running locally

```bash
cd services/regression-detection
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn regression_detection.api.main:app --reload --port 8008
```

## Tests

```bash
pytest
```

- `tests/unit/` — every use case against fakes for the repositories,
  `EvalRunReader`, and `TraceReader`, including the edge cases that drive
  the design: zero-stddev baselines, no prior runs, and insufficient
  trace history for the latency check.
- `tests/integration/test_gate_decisions_api.py`,
  `test_baselines_api.py`, `test_latency_anomaly_api.py` — the FastAPI
  app end-to-end.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repositories against SQLite.

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). See `infra/docker-compose.yml`.
