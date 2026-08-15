# Trident API and persistence migration

## Decision

Trident follows a temporary dual-delivery strategy:

- `app.py` remains the Streamlit compatibility client and regression baseline.
- `api.py` exposes the new FastAPI application boundary.
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
FastAPI enterprise boundary ───┘
                 │
                 └─ ProjectRepository ─ SQLiteProjectRepository
```

The next web client will call FastAPI rather than importing Python services.
This creates a stable boundary for browser applications, internal portals,
workflow plug-ins, mobile clients and background workers.

## Persistence design

`ProjectRepository` is the application-facing contract. SQLite is the first
adapter because it is zero-administration and suitable for local development
and single-instance pilots. The application layer does not import SQLite and
therefore can later use Postgres, managed Postgres or another transactional
store without changing research use cases.

SQLite is not the target for multi-user production. Before production rollout,
add:

1. a Postgres repository implementing the same contract;
2. organization, workspace, user and role tables;
3. object storage for source files and generated reports;
4. migration tooling and row-level authorization;
5. an append-only event and audit log.

## API boundary

The initial API includes:

- `GET /health`
- `GET /v1/capabilities`
- project create, list, read, replace and delete endpoints;
- research-brief generation;
- report-first orchestration.

AI configuration is lazy-loaded. Health checks and project CRUD can operate
without loading model credentials. Model and search credentials are required
only when an AI-backed use case executes.

## Local commands

Compatibility UI:

```bash
streamlit run app.py
```

Enterprise API:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

OpenAPI documentation is available at `/docs` while the API is running.

## Removal gate for Streamlit

Do not delete Streamlit code until all conditions are true:

1. the replacement UI covers build-first and report-review-first paths;
2. project history, enterprise sensing, evidence review, content revision,
   scorecard, action plan and exports reach parity;
3. end-to-end tests pass against the API-backed UI;
4. the deployment has authentication, authorization, database migrations,
   object storage and observability;
5. a rollback window has completed without critical defects.

