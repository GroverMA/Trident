# Trident API and persistence migration

## Decision

Trident follows a temporary dual-delivery strategy:

- `app.py` remains the Streamlit compatibility client and regression baseline.
- `api.py` exposes the new FastAPI application boundary.
- `web/` contains the new Next.js customer client.
- `src/application/` contains delivery-channel-neutral use cases.
- `src/persistence/` contains storage contracts and adapters.
- `src/core/` remains the shared Research Core used by both delivery channels.

The original Industry Analyst repository and its Streamlit deployment are not
part of this migration and must not be changed. Streamlit files in Trident may
only be removed after the replacement web client reaches feature parity and
both research paths pass acceptance tests.

## Current deployment topology

```text
Streamlit compatibility client ─┐
                               ├─ Research Core ─ Providers / SOP / extensions
Next.js client ─ FastAPI API ───┘
                 │
                 └─ ProjectRepository ─┬─ PostgreSQL / Neon (customer environments)
                                      └─ SQLite (development and automated tests)
```

The Next.js Web client calls FastAPI rather than importing Python services.
This creates a stable boundary for browser applications, internal portals,
workflow plug-ins, mobile clients and background workers.

The first migrated vertical slice covers research-path selection, the shared
project brief, project creation, and persisted project retrieval. It intentionally
uses the same API and project record for build-first and report-review-first
workflows so switching the presentation order never forks or discards research.

## Persistence design

`ProjectRepository` is the application-facing contract. PostgreSQL is the
production store; Neon can be used through its standard pooled `DATABASE_URL`.
SQLAlchemy owns connection lifecycle and performs a pre-ping before checkout.
Alembic owns versioned schema migration. In `development` and `test`, a missing
`DATABASE_URL` selects an isolated SQLite database at
`TRIDENT_DATABASE_PATH` (default `data/trident.db`). In `staging` and
`production`, PostgreSQL is mandatory and the service will not silently split
customer data into a local database.

Before broader enterprise rollout, add:

1. organization, workspace, user and role tables;
3. object storage for source files and generated reports;
4. migration tooling and row-level authorization;
4. an append-only event and audit log.

## API boundary

The initial API includes:

- `GET /health` for process liveness;
- `GET /ready` for persistence readiness and explicit degraded status;
- `GET /v1/capabilities`
- project create, list, read, replace and delete endpoints;
- editable research-scope confirmation;
- research-brief generation and human review;
- research-plan generation and human confirmation;
- report-first orchestration.

AI configuration is lazy-loaded. Health checks and project CRUD can operate
without loading model credentials. Model and search credentials are required
only when an AI-backed use case executes.

For Neon staging or production, set `TRIDENT_ENV` and use the pooled connection
string provided by the Neon console as `DATABASE_URL`. Run `alembic upgrade
head` during deployment before starting the API process. If PostgreSQL is
temporarily unavailable, `/health` remains observable while `/ready` returns
503; production does not switch to an unreplicated SQLite database.

## Local commands

Compatibility UI:

```bash
streamlit run app.py
```

Enterprise API:

```bash
# No database configuration is required for local development.
export TRIDENT_ENV=development
uvicorn api:app --host 0.0.0.0 --port 8000
```

Production example (keep the real URL in the hosting platform's secret store):

```bash
export TRIDENT_ENV=production
export DATABASE_URL='postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require'
alembic upgrade head
uvicorn api:app --host 0.0.0.0 --port 8000
```

OpenAPI documentation is available at `/docs` while the API is running.

## Customer-link release gate

The container entry point performs the following sequence before accepting
customer traffic:

1. validate `TRIDENT_ENV`, `PORT`, and worker settings;
2. require `DATABASE_URL` in staging and production;
3. execute all pending Alembic migrations when PostgreSQL is configured;
4. start FastAPI only after migrations succeed;
5. expose `/ready` as the deployment health check.

Customers never configure database credentials. The operator stores
`DATABASE_URL`, model credentials, and search credentials in the hosting
platform's encrypted environment settings. A failed migration stops the new
release before it receives traffic, leaving the previous healthy deployment
available for rollback.

The included `Dockerfile` is platform-neutral. It can be deployed to a managed
container service without changing the research core or persistence adapters.

## Removal gate for Streamlit

Do not delete Streamlit code until all conditions are true:

1. the replacement UI covers build-first and report-review-first paths;
2. project history, enterprise sensing, evidence review, content revision,
   scorecard, action plan and exports reach parity;
3. end-to-end tests pass against the API-backed UI;
4. the deployment has authentication, authorization, database migrations,
   object storage and observability;
5. a rollback window has completed without critical defects.
