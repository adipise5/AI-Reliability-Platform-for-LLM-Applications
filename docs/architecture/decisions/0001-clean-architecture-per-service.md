# ADR-0001: Clean Architecture layering inside every service

## Status
Accepted — 2026-07-19

## Context
The platform is split into fourteen services to avoid a monolith. Without an
internal discipline, each service can still turn into its own small monolith
where FastAPI route handlers call SQLAlchemy directly and business rules
leak into both. That makes scorers, providers, and gate logic hard to unit
test without a database, and hard to swap (e.g. replacing a provider SDK, or
moving from Celery to another queue) without touching business logic.

## Decision
Every service is internally layered as:

- `domain/` — entities, value objects, and *ports* (interfaces) the service
  depends on. No imports from FastAPI, SQLAlchemy, Celery, or any provider
  SDK. Pure Python + the shared `libs/contracts` DTOs.
- `application/` — use cases that orchestrate domain objects through ports.
  Still framework-free; takes its dependencies via constructor injection.
- `infrastructure/` — concrete adapters implementing the ports: database
  repositories, provider SDK clients, cache clients, queue producers.
- `api/` — FastAPI routers, request/response schemas, and the dependency
  wiring that constructs use cases with real adapters.

A CI lint rule enforces that nothing under `domain/` imports a third-party
framework.

## Consequences
- Unit tests for `application/` use cases run against fakes/in-memory
  adapters — no database or network required, so they run in milliseconds
  and don't flake on external API availability.
- Swapping an adapter (a new LLM provider, a different queue) never touches
  `domain/` or `application/`.
- Slightly more boilerplate per service (an interface plus at least one
  implementation) — accepted as the cost of the "independently replaceable"
  constraint from the project brief.
