# Report Generator

Week 11 service. Renders an HTML or PDF report summarizing an
experiment's runs — name, description, and a table of every attached
run's model, status, and score — generated asynchronously via Celery,
the same execution pattern as the Evaluation Engine (Week 6).

## What this service owns (and doesn't)

- **Owns:** `Report` (`reports.reports` — an org-scoped record of one
  render request: format, status, the rendered bytes once ready, and an
  error message if rendering failed).
- **Doesn't own:** experiment or run data. Every report is rendered from
  a fresh call to Experiment Tracking's `GET
  /api/v1/experiments/{id}/comparison` at generation time — there's no
  local cache to go stale.

Requesting a report does no upstream validation before enqueueing (same
reasoning as `TriggerEvalRunUseCase`): the endpoint stays fast, and
`GenerateReportUseCase` fails the report with a clear error if the
experiment doesn't resolve.

## Rendering

Two renderers, chosen by `ReportFormat`:

- **HTML** — a single self-contained page, built directly with f-strings
  (no templating engine — the layout is simple enough that a template
  file would be pure indirection).
- **PDF** — via [fpdf2](https://pypi.org/project/fpdf2/), a pure-Python
  library with no system-level dependencies (no wkhtmltopdf, no
  Cairo/Pango), keeping the Docker image and local setup simple.

Report content is stored as raw bytes directly in Postgres
(`reports.content`, nullable until the report is `ready`) rather than in
an external blob store — consistent with this project's preference for
the simplest storage that works at MVP scale.

## Layering

```
src/report_generator/
├── domain/           Report, RemoteExperimentComparison, errors, ports
├── application/       RequestReportUseCase, GenerateReportUseCase, GetReportUseCase,
│                      ListReportsUseCase, GetReportContentUseCase
├── infrastructure/     HttpExperimentReader, HTML/PDF renderers, SQLAlchemy repository,
│                       Celery worker + task queue, config
└── api/                FastAPI app, routers, schemas, DI wiring
```

## Auth for background execution

Same pattern as the Evaluation Engine: the caller's bearer token is
forwarded as a Celery task argument (never persisted to the database) so
the worker can call Experiment Tracking as the original caller. A report
that takes longer to generate than the token's TTL will fail with an
upstream auth error — use an API key for anything long-running, same
caveat as everywhere else this pattern is used.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `GET /healthz` | none | Liveness check |
| `POST /api/v1/reports` | bearer | Request a report for an experiment; returns immediately with status `pending` |
| `GET /api/v1/reports?experiment_id=` | bearer | List reports for this org, most recent first |
| `GET /api/v1/reports/{id}` | bearer | Report metadata (status, error, timestamps) |
| `GET /api/v1/reports/{id}/content` | bearer | The rendered bytes, `409` if not yet `ready` |

## Running locally

```bash
cd services/report-generator
python -m venv .venv && source .venv/bin/activate
pip install -e ../../libs/auth-client
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn report_generator.api.main:app --reload --port 8009

# in a second terminal, the worker that actually renders reports:
celery -A report_generator.infrastructure.worker worker -Q q.report --loglevel=info
```

## Tests

```bash
pytest
```

- `tests/unit/` — every use case against fakes for the repository,
  `ExperimentReader`, and the renderer registry; the HTML and PDF
  renderers tested directly against a sample comparison; the
  Experiment Tracking client's parsing tested with respx.
- `tests/integration/test_reports_api.py` — the FastAPI app end-to-end.
- `tests/integration/test_repositories.py` — the real SQLAlchemy
  repository against SQLite.

## Docker

Build context is the **repo root** (this service depends on
`libs/auth-client`). See `infra/docker-compose.yml`.
