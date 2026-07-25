# React Dashboard

Week 15. A Vite + React + TypeScript single-page app that talks to two
backend services directly and everything else through one:

- **Auth service** — `POST /api/v1/auth/login` and `POST /api/v1/orgs`,
  called directly from the browser (there's no "auth" concept in the
  Dashboard Backend to proxy through).
- **Report Generator** — `GET /api/v1/reports/{id}/content`, called
  directly to download a report's rendered bytes (the Dashboard Backend
  deliberately doesn't proxy binary content — see its README).
- **Dashboard Backend** — everything else: the overview, eval runs, cost,
  regression, reports metadata, notifications, GitHub checks, traces.

## Auth model

There's no `/me` endpoint anywhere in this project yet, so the frontend
never decodes or introspects the JWT — it just remembers the email you
typed in and the token `POST /api/v1/auth/login` handed back, in
`localStorage`, until the token's own `expires_in` elapses. Signing out
(or an expired token) clears it and the router redirects to `/login` via
`RequireAuth`.

Registering an org (`POST /api/v1/orgs`) doesn't return a session token
by design (see the Auth service) — `RegisterPage` calls `login` with the
same credentials immediately afterward so it still feels like one step.

## Running locally

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Requires the Auth service, the Report Generator, and the Dashboard
Backend (and, transitively, everything *it* fans out to) running and
reachable at the URLs in `.env` — see `infra/docker-compose.yml`. Three
services need CORS enabled for the dev server's origin
(`http://localhost:5173` by default): Auth, Report Generator, and the
Dashboard Backend — each has a `*_CORS_ALLOWED_ORIGINS` setting in its
own `.env.example` for this.

## Layout

```
src/
├── api/          Typed fetch wrappers — client.ts (generic request/ApiError),
│                 auth.ts, dashboard.ts, types.ts (mirrors of the backend's schemas)
├── auth/         AuthContext (session state), LoginPage, RegisterPage, RequireAuth
├── components/   Layout (sidebar nav), StatCard, StatusBadge, LoadingState, ErrorState
├── pages/        One page per Dashboard Backend area — Overview, Runs, RunDetail,
│                 Cost, Regression, Reports, Notifications, GitHubChecks, Traces
└── test/         Vitest setup (jest-dom matchers, Testing Library cleanup)
```

No Redux or other global store — `@tanstack/react-query` owns all
server-state caching, and `AuthContext` is the only client state that
needs to be shared across the app.

## A known gap, inherited from the Dashboard Backend

There's no "browse all prompts" view — Prompt Registry has no
list-all-for-org endpoint yet (see the Dashboard Backend's README). The
Regression page's baseline lookup is a raw prompt-id text field instead
of a picker for this reason; a run's `prompt_id` (shown on its detail
page) is the way to get one to try.

## A known `npm audit` finding

`npm audit` flags `react-router-dom@7.18.1` for a high-severity CSRF
issue in React Router's RSC ("framework") mode
([GHSA-qwww-vcr4-c8h2](https://github.com/advisories/GHSA-qwww-vcr4-c8h2)).
This app uses only the classic declarative `<BrowserRouter>`/`<Routes>`
API — no server actions, no RSC, no framework-mode data loaders — so the
vulnerable code path is never reached. The alternative (pinning to an
older 7.x version) trades this for a much longer list of flagged
advisories in that range, several of which are equally inapplicable but
some of which aren't as clearly so; staying on latest was the better
trade here. Revisit if React Router ships a patched 7.x/8.x release.

## Tests

```bash
npm test
```

Vitest + React Testing Library. `test.globals` is deliberately left off
in `vite.config.ts`, so `src/test/setup.ts` registers Testing Library's
DOM cleanup via an explicit `afterEach` rather than relying on
auto-detection.

The `test` script also sets `NODE_OPTIONS=--no-webstorage`: Node 24+
ships its own experimental global `localStorage`, backed by a file that
isn't configured here, which silently shadows jsdom's working
implementation and breaks anything that touches `localStorage` (which
`AuthContext` does, for persisting the session). Disabling Node's own
version lets jsdom's take over.

## What's not automated

Every backend service in this project has a pytest suite that runs
against fakes with no live infrastructure. This frontend's tests follow
the same shape (mocked API modules, no real network calls) but there is
no browser-driven end-to-end test exercising the full stack — the repo
sandbox this was built in has no running Postgres/Redis/Docker to spin
one up against. `npm run build` (a real `tsc -b && vite build`) and
`npm test` are what's been verified; a real login → dashboard →
run-detail click-through against live services has not.
