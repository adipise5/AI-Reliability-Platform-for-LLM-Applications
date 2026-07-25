
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

Pre-release. Built incrementally, one service per week, per the plan in
[`docs/architecture/overview.md`](docs/architecture/overview.md). Weeks 1–12
are done; **Week 13 — GitHub Integration** is next.

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
| 13 | GitHub Integration | ⬜ not started |
| 14 | Dashboard Backend | ⬜ not started |
| 15 | React Dashboard | ⬜ not started |
| 16 | Hardening & v1.0 release | ⬜ not started |

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
libs/         shared kernel: contracts, otel instrumentation, auth client
frontend/     React dashboard (from Week 15)
infra/        docker-compose, Kubernetes manifests, Prometheus/Grafana config
docs/         architecture docs, ADRs, generated OpenAPI specs
```

## Running locally

Each service is independently runnable; see its own `README.md` under `services/<name>/`
for setup. A combined `infra/docker-compose.yml` grows as services come online — it
currently brings up PostgreSQL, Redis, the Authentication Service, Prompt Registry,
Dataset Management, the Trace Collector, the Gateway, the Evaluation Engine
(API + Celery worker), Hallucination / Faithfulness Detection, Experiment Tracking,
Cost & Token Analytics, the Regression Detection Engine, the Report Generator
(API + Celery worker), and the Notification Service (API + Celery worker).

Gateway, Prompt Registry, Dataset Management, the Evaluation Engine, Hallucination
Detection, Experiment Tracking, Cost Analytics, Regression Detection, the Report
Generator, and the Notification Service all depend on the shared `libs/auth-client`
package. Install it before each service's own dependencies:
`pip install -e libs/auth-client` — see the affected services' READMEs.

## License

MIT — see [`LICENSE`](LICENSE).
