# Deployment

Two ways to run this platform, for two different purposes.

## Local development — `infra/docker-compose.yml`

One command brings up every service, Postgres, Redis, Prometheus, and a
pre-provisioned Grafana:

```bash
cd infra
docker compose up --build
```

Before that, copy every service's `.env.example` to `.env`
(`cp services/gateway/.env.example services/gateway/.env`, repeated for
each `services/*`) — real secrets and API keys come from those files;
`docker-compose.yml` only overrides the network-internal values (DB
host, other services' URLs) that have to match the compose network.

Once it's up:

| What | Where |
|---|---|
| Gateway | http://localhost:8000 |
| Dashboard Backend (the BFF the React app talks to) | http://localhost:8013 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin — see ADR-0007) |
| React Dashboard | not part of compose — `cd frontend && npm run dev`, see `frontend/README.md` |

Every other service's port is listed in `infra/docker-compose.yml`
(8001–8013) and in its own `README.md`.

## Kubernetes / production — `infra/k8s/helm/`

A generic chart (`service-chart/`) aliased once per deployable unit by an
umbrella chart (`platform/`) — see ADR-0008 for why one chart instead of
17, and `infra/k8s/helm/README.md` for install steps (build/push images,
fill in `values-secrets.yaml`, `helm install`).

Deliberately doesn't bundle Postgres/Redis — point the platform at
whatever you've actually provisioned (managed service, separately
installed chart, existing cluster resource). Also deliberately doesn't
assume a Prometheus Operator is installed; if one is, replace
`infra/prometheus/prometheus.yml`'s static scrape config with a
`ServiceMonitor` per service (matching the same `GET /metrics` path) —
not included here since whether that CRD exists is a property of the
target cluster, not of this platform.

## Observability

See [ADR-0007](architecture/decisions/0007-prometheus-metrics-and-grafana-dashboards.md)
for what's instrumented (every FastAPI service's `GET /metrics`, via
`prometheus-fastapi-instrumentator`) and what isn't yet (the 3 Celery
workers — they run no HTTP server, so the same instrumentation approach
doesn't apply to them without a separate mechanism).

Two dashboards ship pre-provisioned in `infra/grafana/dashboards/`:

- **Service HTTP Overview** — request rate, error rate, latency
  percentiles for any one service, picked via a dashboard variable.
- **Cost & Token Analytics** — spend and token usage, queried directly
  from Postgres rather than from a Prometheus metric (see the ADR for
  why that split makes sense here).

## What's been verified vs. what hasn't

Every service's own test suite (pytest + ruff + mypy --strict) passes —
see each `services/<name>/README.md`. The Helm chart's `helm lint` and
`helm template` output has been checked structurally (right resource
counts, no name collisions, correct per-alias overrides — see
`infra/k8s/helm/README.md`). None of this — the full docker-compose
stack, Prometheus actually scraping all 14 services, Grafana's
dashboards actually rendering data, or the Helm chart applied to a real
cluster — has been exercised live end-to-end in this repo's sandbox,
which has no running Docker daemon or Kubernetes cluster. If you're
picking this up to actually deploy it, that live pass is the next real
step, not an assumption already covered here.
