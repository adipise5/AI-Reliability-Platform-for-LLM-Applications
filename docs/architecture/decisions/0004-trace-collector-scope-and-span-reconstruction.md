# ADR-0004: Trace Collector is OTel-shaped (not OTLP), open (not authenticated) — and the Gateway reconstructs spans after the fact

## Status
Accepted — 2026-07-19 (Week 5)

## Context
Week 5 needed the Gateway to be observable end-to-end. Three separate
scope questions came up building that, all worth recording together since
they're one decision cluster:

1. Should the Trace Collector speak real OTLP (the OpenTelemetry wire
   protocol), so any OTel Collector or vendor backend could ingest from
   it directly?
2. Should ingestion and query be authenticated?
3. `RouteChatUseCase`/`StreamChatUseCase` call `TracingSink.emit_span(name,
   status, duration_ms, attributes)` once, from a `finally` block, after
   the operation has already completed — they don't hold a live span
   object across the call the way `with tracer.start_as_current_span():`
   normally works. Does adopting real OTel require reworking that?

## Decisions

**1. OTel-shaped, not OTLP-compliant.** Spans carry the same concepts the
OpenTelemetry SDK produces — trace/span id, parent, name, status, timing,
flat attributes — but `POST /api/v1/traces` accepts a small custom JSON
batch, not OTLP protobuf. A full OTLP receiver is a self-contained later
swap of the Trace Collector's ingestion adapter; nothing in the domain
model changes when it happens.

**2. No auth yet.** Both ingestion and query are open. Two direct
consequences, both deferred on purpose: no per-org scoping (spans aren't
attributed to an org — the Gateway's `AuthContext` doesn't carry one
either, see ADR-0003), and no inter-service authentication. A nullable
`org_id` column added now, before anything reads or writes it, would be
dead weight; it lands with the Dashboard Backend (Week 14). Inter-service
auth is a Week 16 hardening concern, once every service that needs to
call another exists.

**3. The Gateway reconstructs spans after the fact.** Rather than
threading a live OTel span through `RouteChatUseCase`/`StreamChatUseCase`
— which would mean changing their `execute()` signatures and every
existing Week 1 test — `OtelTracingSink.emit_span` opens a span with an
explicit `start_time` computed by subtracting `duration_ms` from now,
sets attributes and status, and immediately ends it with an explicit
`end_time`. The resulting span is indistinguishable, once it reaches an
exporter, from one produced the context-manager way.

## Consequences
- Ingesting into a real OTel Collector later means writing an OTLP-shaped
  ingestion adapter for the Trace Collector; the `Span`/`TraceSummary`
  domain model and every use case built this week are unaffected.
- Trace data currently has no tenant boundary — anyone who can reach the
  service on the network can read every trace. This is fine for a
  single-tenant local/dev deployment and explicitly not fine beyond that;
  tracked as a known gap, not a silent one.
- The post-hoc span reconstruction means the Gateway never holds a span
  open across an `await` — there's no risk of a span leaking across
  concurrent requests via incorrect context propagation, which the
  context-manager style has to get right. The tradeoff is that nested
  child spans (e.g. a sub-span specifically for the provider HTTP call)
  aren't possible without revisiting this — not needed yet, since each
  Gateway call is currently a single flat span.
