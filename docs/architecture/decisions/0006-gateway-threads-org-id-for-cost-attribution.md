# ADR-0006: The Gateway threads `org_id` from auth through to usage (and trace) events

## Status
Accepted — 2026-07-19 (Week 9)

## Context
ADR-0004 (Week 5) deliberately left `org_id` off the Gateway's `AuthContext`
and off Trace Collector spans, on the grounds that nothing read it yet and
a column nobody queries is dead weight. Week 9's Cost Analytics service is
the first real consumer: a cost ledger with no tenant attribution isn't a
cost ledger, it's a number. This ADR records closing that gap rather than
letting Cost Analytics invent its own notion of "whose request was this."

## Decision
`AuthContext` (`gateway/domain/entities.py`) gains an `org_id: str` field.
Both adapters populate it:

- `RemoteAuthServiceAdapter` already receives `org_id` on every
  introspection response (`auth_client.IntrospectionResult.org_id`) and
  was simply discarding it — now it's passed through.
- `StaticAPIKeyAuthAdapter` (the dev-only fallback, ADR-0003) has no real
  org concept, so it reports a fixed placeholder, `"static-dev-org"` —
  fine for local, single-tenant use, wrong for anything else, which is
  exactly the deal every static-key limitation in this codebase makes
  explicit rather than hides.

`RouteChatUseCase.execute()`/`StreamChatUseCase.execute()` take `org_id`
as an explicit parameter (from the router, which reads it off
`AuthContext`) and forward it to `UsageSink.emit_usage()` — a new
parameter on that port — and add it to the trace span's attributes, since
it's now available at the same call site for free and Trace Collector
already stores arbitrary attributes.

## Consequences
- Cost Analytics can roll up spend per org from day one instead of
  needing a follow-up migration once multi-tenant billing actually
  matters.
- Every Gateway unit test that builds an `AuthContext`, a fake `UsageSink`,
  or calls a use case's `execute()` needed updating for the new parameter
  — a real, one-time cost of not adding the field speculatively back in
  Week 5. Paid once, now.
- `HttpCostAnalyticsUsageSink.emit_usage` swallows its own exceptions
  (logs and returns) rather than propagating — a chat request must never
  fail because the cost ledger is down, the same principle behind the
  OTel exporter's "never raise" contract (ADR-0004). Unlike tracing,
  though, this call is still awaited inline rather than backgrounded
  through a batching layer, so a slow or down Cost Analytics adds latency
  to every chat call rather than none. Backgrounding it properly would
  mean giving the Gateway its own queue — not justified yet for one
  best-effort POST, and noted here as a known tradeoff rather than a
  silent one.
