# Trace Collector

Week 5 service. Ingests OTel-*shaped* spans, stores them, and exposes a
basic trace viewer API. The Gateway's `OtelTracingSink` (see its
`infrastructure/observability/`) is the first real producer — every
Gateway call is observable end-to-end from this week on.

"OTel-shaped, not OTLP-compliant" is a deliberate scope cut: spans carry
the same concepts the OpenTelemetry SDK produces (trace/span id, parent,
name, status, timing, flat attributes), but ingestion speaks a small
custom JSON batch shape rather than the OTLP protobuf wire format. A full
OTLP receiver is a later, self-contained swap of the ingestion adapter —
see `domain/entities.py`'s module docstring.

## Layering

```
src/trace_collector/
├── domain/           Span, SpanStatus, TraceSummary, errors, ports
├── application/      IngestSpansUseCase, GetTraceUseCase, ListTracesUseCase
├── infrastructure/   SQLAlchemy models/repository, config
└── api/              FastAPI app, routers, schemas, DI wiring
```

## Auth (there isn't any, yet)

Both ingestion and query are open in this MVP — same class of "trusted
internal network" reasoning as the Authentication Service's own
`/introspect` endpoint. Two things are missing as a direct consequence,
both deferred on purpose rather than faked:

- **No per-org scoping.** Spans aren't attributed to an org today (the
  Gateway's `AuthContext` doesn't carry one either — see ADR-0003). Adding
  a nullable `org_id` column now, before anything reads or writes it,
  would just be dead weight; it lands when the Dashboard Backend (Week 14)
  needs per-org trace views.
- **No inter-service authentication.** Any service on the network can
  ingest or read traces. A hardening pass (Week 16) is the natural place
  to add one, once every service that needs to call another exists.

## Model

- **Span** — one OTel-shaped span: `trace_id`/`span_id`/`parent_span_id`,
  `name`, `status` (`UNSET`/`OK`/`ERROR`), start/end time, flat attributes.
- **TraceSummary** — a read-model computed from a trace's spans, not a
  stored row: root span name, span count, a rolled-up status (`ERROR` if
  any span errored), start time, total duration.

`list_recent_trace_ids` + one `get_by_trace_id` per id (an N+1 query
pattern) is how `ListTracesUseCase` builds summaries, rather than a single
aggregate SQL query — at this stage's expected trace volume that's a
perfectly fine tradeoff, and it keeps the summary-building logic in the
domain layer instead of a hand-rolled cross-dialect SQL aggregate.

## Endpoints

| Method & path | Description |
|---|---|
| `GET /healthz` | Liveness check |
| `POST /api/v1/traces` | Ingest a batch of spans; `202 Accepted` |
| `GET /api/v1/traces?limit=` | Recent trace summaries, most recent first |
| `GET /api/v1/traces/{trace_id}` | Every span belonging to one trace |

## Running locally

```bash
cd services/trace-collector
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

alembic upgrade head
uvicorn trace_collector.api.main:app --reload --port 8004
```

## Tests

```bash
pytest
```

`tests/unit/` (fakes), `tests/integration/test_traces_api.py` (FastAPI
end-to-end), `tests/integration/test_repositories.py` (real SQLAlchemy
repository against SQLite).

## Docker

```bash
docker build -t arp-trace-collector .
docker run -p 8004:8000 --env-file .env arp-trace-collector
```

Or via `infra/docker-compose.yml`.
