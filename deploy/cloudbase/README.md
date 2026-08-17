# Trident CloudBase China Demo

This deployment keeps the existing Vercel deployment unchanged. CloudBase builds
the same repository with `deploy/cloudbase/Dockerfile` and exposes one default
CloudBase domain. The Next.js web workspace proxies API requests to the FastAPI
process inside the same container.

## CloudBase resources

1. One CloudBase environment in the Hong Kong region when available.
2. One CloudBase container service built from this GitHub repository.
3. One Serverless MySQL database for durable project memory.
4. CloudBase object storage for raw enterprise files in the next deployment step.

## Build settings

- Repository: `GroverMA/Trident`
- Branch: `codex/cloudbase-demo` for trial deployment
- Build context: repository root
- Dockerfile: `deploy/cloudbase/Dockerfile`
- Container port: `3000`
- Health path: `/`

## Required environment variables

- `TRIDENT_ENV=production`
- `DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE?charset=utf8mb4`
- `HKGAI_API_KEY`
- `HKGAI_MODEL`
- `HKGAI_BASE_URL`
- `SEARCH_AGENT_APP_NAME`
- `SEARCH_AGENT_APP_KEY`

Keep credentials in CloudBase environment variables. Never commit them to Git.

## Deployment behavior

The container runs database migrations before starting. FastAPI listens only on
the container loopback address at port 8000. Next.js is the public process at
port 3000, so the browser sees one origin and one CloudBase default domain.
