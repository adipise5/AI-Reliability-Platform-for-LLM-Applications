# Evaluation Engine

Week 6 service — the first one that's actually asynchronous. Triggering a
run returns immediately (`202 Accepted`); a Celery worker does the real
work: fetching a pinned prompt version and dataset from their owning
services, calling the Gateway once per dataset item, scoring each result,
and recording everything.

This is also the first service to call *other application services*
(Prompt Registry, Dataset Management, the Gateway) rather than just the
Authentication Service — see "Auth for background execution" below for
how that interacts with credentials.

## Layering

```
src/evaluation_engine/
├── domain/           EvalRun, RunItemResult, Score, remote value objects, ports
├── application/      TriggerEvalRunUseCase, ExecuteEvalRunUseCase, GetEvalRunUseCase
├── infrastructure/
│   ├── clients/       HTTP clients to Prompt Registry, Dataset Management, the Gateway
│   ├── scorers/        ExactMatchScorer, LLMJudgeScorer, InMemoryScorerRegistry
│   ├── worker.py        the Celery app + the one task that executes a run
│   └── task_queue.py     the FastAPI-side `TaskQueue` port adapter (enqueues by task name)
└── api/              FastAPI app, routers, schemas, DI wiring
```

## Auth for background execution

`ExecuteEvalRunUseCase` needs to call Prompt Registry, Dataset Management,
and the Gateway *as the org that triggered the run* — those services are
org-scoped by whichever credential calls them. Rather than inventing a
service-to-service identity, the Evaluation Engine forwards the same
bearer credential the caller used to trigger the run:

- The credential is passed as a **Celery task argument**, not stored on
  the `eval_runs` row — it lives in the queue message (Redis), never in
  Postgres, the durable store.
- **Use an API key, not a short-lived session JWT, to trigger runs that
  might outlive the JWT's TTL.** A run that takes longer than
  `AUTH_JWT_TTL_SECONDS` to reach a given item will start failing
  upstream calls with `401`s from a credential that expired mid-run.
  API keys don't expire, which is exactly the CI/automation use case this
  is for.

A real hardening pass would replace this with a short-lived, run-scoped
service token minted at trigger time instead of forwarding the caller's
own credential — noted here as a known simplification, not a silent one.

## Scorers

Three ship as of Week 7, all behind the same `Scorer` port:

- **`exact_match`** — string equality after trimming. Good for
  golden-answer datasets; free-form generation needs one of the others.
- **`llm_judge`** — asks a judge model (`EVAL_ENGINE_JUDGE_MODEL`, called
  through the same Gateway every run uses) to grade the output 0–1
  against the expected answer, at `temperature=0` to minimize the judge's
  own variance. Judge quality drifting across model versions is a real,
  unsolved limitation — see the risk register in
  `docs/architecture/overview.md`.
- **`faithfulness`** — delegates to the Week 7 Hallucination / Faithfulness
  Detection service (`EVAL_ENGINE_HALLUCINATION_SERVICE_URL`), which
  extracts the response's claims and checks each against a context
  passage. Only meaningful when a dataset item's `input` carries a
  `context` field (the passage a RAG-style response should be grounded
  in) — items without one score vacuously faithful (`1.0`, nothing to
  contradict), the same convention that service uses internally.

An `EvalRun` records which scorer names ran (`scorer_names`, defaults to
`("exact_match",)`); `aggregate_score` is the mean of every score from
every scorer across every item — deliberately simple for this milestone.

## Failure model

Fail-fast, deliberately: if rendering the template for one dataset item
fails (a missing template variable) or a Gateway call errors, the *whole
run* is marked `failed` with the exception message recorded. Partial-run
tolerance — score what succeeded, flag what didn't — is a reasonable
follow-up but adds real complexity (per-item status, partial-aggregate
semantics) not needed to make the engine useful yet.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/runs` | bearer | Trigger a run; `202` + the `pending` run record |
| `GET /api/v1/runs?prompt_id=&dataset_id=` | bearer | List runs, most recent first — what Experiment Tracking (Week 8) is built on |
| `GET /api/v1/runs/{id}` | bearer | Run status/metadata plus every item result so far |

## Running locally

Needs PostgreSQL, Redis, and the Auth/Prompt-Registry/Dataset-Management/
Gateway services reachable:

```bash
cd services/evaluation-engine
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn evaluation_engine.api.main:app --reload --port 8005   # API
celery -A evaluation_engine.infrastructure.worker worker -Q q.evaluation --loglevel=info  # worker, separate terminal
```

## Tests

```bash
pytest
```

- `tests/unit/` — `TriggerEvalRunUseCase` and `ExecuteEvalRunUseCase`
  against fakes for every port (repos, the three HTTP clients, the
  scorer registry) — the full orchestration logic runs with no network
  and no Celery/Redis at all.
- `tests/integration/test_runs_api.py` — the FastAPI app end-to-end, with
  the use cases' dependencies overridden.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repositories against SQLite.

Celery/Redis themselves aren't exercised by the test suite — the task
(`infrastructure/worker.py`) is a thin `asyncio.run()` wrapper around
`ExecuteEvalRunUseCase`, which is exactly what's under test; see that
module's docstring for why the engine can't be shared across task
invocations.

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). Run two containers from the same image — see
`infra/docker-compose.yml` for how the worker's `command:` differs from
the API's default `CMD`.
