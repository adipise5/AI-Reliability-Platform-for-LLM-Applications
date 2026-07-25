
# AI Reliability Platform

A modular, self-hostable control plane that continuously evaluates, monitors, and
validates LLM applications across Claude, GPT, Gemini, and local Llama/Ollama models —
before and after deployment.

This is not a chatbot. It is a CI gate, an observability stack, and an evaluation lab
for production AI systems: prompt versioning, golden datasets, automated evaluation,
regression detection, hallucination/faithfulness scoring, cost and token analytics,
distributed tracing, and Slack/GitHub-integrated reporting — each as an independently
replaceable service.

## Status

**v1.0.** Built incrementally, one service per week, per the plan in
[`docs/architecture/overview.md`](docs/architecture/overview.md). All 16 weeks are
done — see [ADR-0007](docs/architecture/decisions/0007-prometheus-metrics-and-grafana-dashboards.md)
and [ADR-0008](docs/architecture/decisions/0008-kubernetes-deployment-shared-chart.md)
for Week 16's observability and Kubernetes-deployment decisions, and
[`docs/deployment.md`](docs/deployment.md) for what's been verified vs. what a real
rollout still needs to check for itself (this repo's sandbox has no live cluster or
Docker daemon to exercise the full stack against).

| Week | Service | Status |
|---|---|---|
| 01 | AI Gateway | ✅ done |
| 02 | Authentication Service | ✅ done |
| 03 | Prompt Registry | ✅ done |
| 04 | Dataset Management | ✅ done |
| 05 | Trace Collector | ✅ done |
| 06 | Evaluation Engine | ✅ done |
| 07 | Hallucination / Faithfulness Detection | ✅ done |
| 08 | Experiment Tracking | ✅ done |
| 09 | Cost & Token Analytics | ✅ done |
| 10 | Regression Detection Engine | ✅ done |
| 11 | Report Generator | ✅ done |
| 12 | Notification Service | ✅ done |
| 13 | GitHub Integration | ✅ done |
| 14 | Dashboard Backend | ✅ done |
| 15 | React Dashboard | ✅ done |
| 16 | Hardening, Prometheus/Grafana, Helm/k8s, docs, v1.0 | ✅ done |

## Architecture

See [`docs/architecture/overview.md`](docs/architecture/overview.md) for the full
system design (service catalog, bounded contexts, database schema, API conventions,
event/queue architecture, deployment) and [`docs/architecture/decisions/`](docs/architecture/decisions/)
for the reasoning behind specific choices.

Guiding constraints, in short:

- **No monolith.** Fourteen independently deployable services, each owning its own
  database schema and REST API.
- **Clean Architecture per service.** `domain → application → infrastructure → api`
  layering; the domain layer never imports a framework or an ORM.
- **Domain-Driven Design at the seams.** Service boundaries are bounded contexts.
- **CI-native.** The GitHub Action regression gate is a first-class product surface,
  not a bolt-on.
- **LangGraph is deferred.** Reserved for an optional, later AI debugging assistant —
  it does not touch the gateway or evaluation core.

## Repository layout

```
services/     one folder per deployable service (see overview.md for the list)
libs/         shared kernel — just auth-client; see the note below
frontend/     React dashboard (Week 15)
infra/        docker-compose, Helm/Kubernetes manifests, Prometheus/Grafana config
docs/         architecture docs, ADRs, deployment guide, generated OpenAPI specs
```

`libs/` originally scaffolded `contracts/`, `otel-instrumentation/`, and
`testing-fixtures/` alongside `auth-client/` — all three stayed empty. OTel
instrumentation ended up living directly in each service's own
`infrastructure/observability/` (see ADR-0004), request/response contracts turned
out to be per-service Pydantic schemas rather than a shared package, and the
SQLite-repository-test pattern (see ADR-0002) is copy-pasted per service's
`tests/integration/` rather than shared — each a case of the actual implementation
finding a better seam than the one guessed at during initial planning. Removed
rather than left as dead scaffolding.

## Running locally

See [`docs/deployment.md`](docs/deployment.md) for the full picture (docker-compose
for local dev, Helm/Kubernetes for a real deployment, Prometheus/Grafana access). In
short: each service is independently runnable — see its own `README.md` under
`services/<name>/` for setup — and a combined `infra/docker-compose.yml` brings up
PostgreSQL, Redis, Prometheus, a pre-provisioned Grafana, the Authentication Service,
Prompt Registry, Dataset Management, the Trace Collector, the Gateway, the Evaluation
Engine (API + Celery worker), Hallucination / Faithfulness Detection, Experiment
Tracking, Cost & Token Analytics, the Regression Detection Engine, the Report
Generator (API + Celery worker), the Notification Service (API + Celery worker), the
GitHub Integration service, and the Dashboard Backend.

Gateway, Prompt Registry, Dataset Management, the Evaluation Engine, Hallucination
Detection, Experiment Tracking, Cost Analytics, Regression Detection, the Report
Generator, the Notification Service, GitHub Integration, and the Dashboard Backend
all depend on the shared `libs/auth-client` package. Install it before each service's
own dependencies: `pip install -e libs/auth-client` — see the affected services'
READMEs.

The React Dashboard (`frontend/`) is a separate Vite dev server, not part of
`infra/docker-compose.yml` — see `frontend/README.md` for setup. It talks to the Auth
service, the Report Generator, and the Dashboard Backend directly over HTTP, so those
three need `*_CORS_ALLOWED_ORIGINS` set to the dashboard's origin (defaults to
`http://localhost:5173`, already the default in each service's `.env.example`).

## License

MIT — see [`LICENSE`](LICENSE).
