# ADR-0002: One PostgreSQL cluster, one schema per service

## Status
Accepted — 2026-07-19

## Context
Fourteen services each need durable storage. Running fourteen separate
Postgres instances is the "purest" microservice answer but is heavy
operational overhead for a self-hosted OSS platform, especially in the
Docker Compose reference deployment aimed at individual users and small
teams.

## Decision
Use a single PostgreSQL cluster with one schema per service (e.g.
`prompt_registry`, `eval_engine`, `cost_analytics`). Each service:

- owns migrations for its schema only,
- connects with a role scoped to its own schema,
- never queries another service's tables directly — cross-service reads go
  through that service's REST API, cross-service reactions go through a
  domain event (see the event architecture in `overview.md`).

A CI check greps each service's SQLAlchemy models/migrations for references
to another service's schema and fails the build if found.

## Consequences
- Local dev and the reference Docker Compose deployment need exactly one
  Postgres container.
- The boundary that matters (no cross-schema queries) is enforced the same
  way whether schemas share a cluster or not, so splitting a service onto
  its own database instance later is a connection-string change, not a
  rewrite.
- A single cluster is a shared failure domain and a shared scaling
  bottleneck; acceptable at OSS/self-hosted scale, called out as a scaling
  limit in the design's risk register.
