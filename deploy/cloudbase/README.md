# Trident CloudBase China Demo (SQLite)

This deployment keeps the existing Vercel deployment unchanged. CloudBase builds
the same repository with `deploy/cloudbase/Dockerfile` and exposes one default
CloudBase domain. The Next.js web workspace proxies API requests to the FastAPI
process inside the same container.

## CloudBase resources

1. One CloudBase environment in the Hong Kong region when available.
2. One CloudBase container service built from this GitHub repository.
3. One persistent storage mount for the SQLite demo database.
4. CloudBase object storage for raw enterprise files in a later deployment step.

## Build settings

- Repository: `GroverMA/Trident`
- Branch: `codex/cloudbase-demo` for trial deployment
- Service name: `trident-agent-cn`
- Target directory / build context: leave blank (repository root)
- Dockerfile: `deploy/cloudbase/Dockerfile`
- Access port: `80`
- Service port: `3000`
- Health path: `/`
- Public default domain: enabled

## Required environment variables

- `TRIDENT_ENV=production`
- `TRIDENT_DATABASE_MODE=sqlite`
- `TRIDENT_DATABASE_PATH=/app/data/trident.db`
- `WEB_CONCURRENCY=1`
- `HKGAI_MODEL_API_KEY`
- `HKGAI_MODEL_NAME=t2_hkgai-v3_fp8_1m_e7`
- `HKGAI_MODEL_BASE_URL=https://test-new-api.hkchat.app`
- `HKGAI_APP_NAME`
- `HKGAI_APP_KEY`

Do not set `DATABASE_URL` for this SQLite demo. Keep credentials in CloudBase
environment variables and never commit them to Git.

## Runtime and storage settings

- Mount persistent storage at `/app/data`. Without this mount, projects can be
  lost when the container restarts or is redeployed.
- Keep the maximum instance count at `1`; SQLite must not be written by multiple
  container instances.
- Low-cost demo: automatic scaling, minimum `0`, maximum `1`.
- More responsive demo: minimum `1`, maximum `1`.

## Deployment behavior

The SQLite demo skips PostgreSQL migrations. FastAPI listens only on the
container loopback address at port 8000. Next.js is the public process at port
3000, so the browser sees one origin and one CloudBase default domain.

When CloudBase later provides a writable PostgreSQL connection, switch to
`TRIDENT_DATABASE_MODE=database_url`, add `DATABASE_URL`, remove the SQLite path,
and then allow multiple worker or container instances.
