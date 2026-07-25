# ADR-0007: Prometheus metrics via a shared instrumentator, two Grafana dashboards

## Status
Accepted — 2026-07-25 (Week 16)

## Context
Every FastAPI service has structured error handling and a `GET /healthz`,
but nothing exposed request rate, error rate, or latency anywhere — the
original spec named Prometheus/Grafana as part of the stack from the
start, and Week 16 ("hardening & v1.0 release") is the natural point to
close that gap rather than ship v1.0 with no operational visibility at
all.

## Decision
**Instrumentation.** `prometheus-fastapi-instrumentator` added to all 14
FastAPI services (not the Celery workers — see Consequences), wired with
two lines in each `api/main.py`:

```python
Instrumentator().instrument(app).expose(app)
```

This is deliberately *not* a shared `libs/` package. Two lines repeated
14 times is cheaper to read, grep, and reason about per-service than a
shared wrapper would be to design, version, and depend on — the same
judgment call this project has made everywhere else (see `libs/`'s only
real member, `auth-client`, which earns its shared-package status by
being genuinely nontrivial: JWT introspection, a FastAPI dependency with
a documented gotcha, retry/error handling). This gives every service
`GET /metrics` with standard `http_requests_total` /
`http_request_duration_seconds` histograms, labeled by handler, method,
and status — enough to build one dashboard that works for any of them.

**Scraping.** `infra/prometheus/prometheus.yml` — one static target per
service, docker-compose hostnames. This is explicitly a dev/docker-compose
convenience, not what a real cluster would use (see ADR-0008's Helm
chart notes on `kubernetes_sd_configs` / a `ServiceMonitor` instead).

**Dashboards.** Two, deliberately different in kind:
- `service-http-overview.json` — infra metrics from Prometheus, templated
  by a `$service` variable so one dashboard covers all 14 services rather
  than needing 14 near-identical copies.
- `cost-analytics.json` — business metrics (spend, token usage) queried
  **directly from Postgres** (`cost_analytics.usage_records`) via
  Grafana's own Postgres data source, not from a Prometheus metric. Spend
  is inherently a stored, queryable fact already owned by a service's own
  database — turning it into a Prometheus gauge would mean a service
  either polling its own DB on a timer to update a gauge (redundant
  computation, staleness between polls) or Cost Analytics growing a
  metrics-exporter responsibility it doesn't otherwise need. Querying the
  database Grafana already has a connection to is the simpler path, and
  demonstrates the platform supports both kinds of dashboard.

Both provisioned automatically (`infra/grafana/provisioning/`) so
`docker compose up` gives a working Prometheus + Grafana out of the box,
no manual "add a data source" click-through step.

## Consequences
- Celery workers (the evaluation-engine, report-generator, and
  notification-service workers) emit no metrics yet — they run no HTTP
  server, so `prometheus-fastapi-instrumentator` (which instruments a
  FastAPI *app*) doesn't apply. Worker-side metrics (task duration, queue
  depth, failure rate) would need a different mechanism — Celery's own
  signal hooks feeding a `prometheus_client` registry pushed via a
  pushgateway, or `celery-prometheus-exporter` — deliberately left as a
  follow-up rather than bolted on speculatively here.
- The Postgres data source's credentials in `infra/grafana/provisioning/datasources/datasources.yml`
  are the same dev-only `auth`/`auth` pair `docker-compose.yml`'s Postgres
  container uses everywhere else in this repo — fine for local dev,
  something a real deployment must override (same caveat as every other
  checked-in dev credential in this project).
- Grafana's default admin/admin login (`docker-compose.yml`'s
  `GF_SECURITY_ADMIN_*`) is the same story — change it before exposing
  Grafana beyond a local machine.
