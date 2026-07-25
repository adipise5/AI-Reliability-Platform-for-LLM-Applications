# ADR-0005: Evaluation Engine owns run results; credentials flow through the task queue, never the database

## Status
Accepted — 2026-07-19 (Week 6)

## Context
The original v0.1 design (`docs/architecture/overview.md`) split run data
across two services: Evaluation Engine would own `eval_runs`,
`scorer_registrations`, and `run_queue_state` (orchestration), while
Experiment Tracking (Week 8) would own `experiments`, `runs`,
`run_item_results`, and `scores` (the actual results). Building a working
Evaluation Engine this week surfaced two problems with that split as
originally drawn.

## Decisions

**1. Evaluation Engine owns `eval_runs` and `run_item_results` directly.**
Experiment Tracking doesn't exist yet, and an Evaluation Engine that can't
persist what it just computed isn't a working service. Rather than block
Week 6 on a service two milestones away, the Evaluation Engine's own
`eval_engine` schema owns both the run record and the per-item results
(with scores embedded as JSON on the result row — a small, always-fetched-
together list with no independent lifecycle, not worth a join table).
Week 8's Experiment Tracking becomes a **comparison and aggregation layer**
that reads across runs (via the Evaluation Engine's own API), rather than
a second store duplicating the same write path. This is a refinement of
the v0.1 draft, not a reversal of it — the service that runs an
evaluation owning the result of running it is a more direct match for
Clean Architecture's data-ownership rule than splitting write and read
across two services from day one.

**2. The triggering credential travels through the task queue message,
never through the database.** `ExecuteEvalRunUseCase` calls Prompt
Registry, Dataset Management, and the Gateway *as the org that triggered
the run* — those services are org-scoped by whatever credential calls
them. `TriggerEvalRunUseCase` passes the caller's bearer credential as a
Celery task argument (Redis-backed, transient) rather than persisting it
on the `eval_runs` row (Postgres, durable). See the service's own README
("Auth for background execution") for the direct consequence: a run
triggered with a short-lived session JWT can start failing partway
through if it outlives the token's TTL, so CI/automation should trigger
runs with an API key instead.

## Consequences
- Week 8 (Experiment Tracking) is now scoped as an aggregation/comparison
  service from the start, not a data-owning one — its own ADR should
  revisit this if a future need (e.g. cross-run analytics at a scale the
  Evaluation Engine's schema doesn't serve well) argues for materializing
  its own copy.
- No bearer credential is ever written to a database in this platform —
  Postgres backups, replicas, and any future data-warehouse export never
  carry live secrets. The tradeoff is real: a run's credential is exactly
  as long-lived as the token forwarded to it, which is a real operational
  constraint documented rather than hidden.
- A production hardening pass would replace credential-forwarding with a
  short-lived, run-scoped service token minted at trigger time — noted as
  a known simplification, matching the same honesty standard as the
  Trace Collector's open endpoints (ADR-0004) and the Gateway's Week 1
  static-key fallback (ADR-0003).
