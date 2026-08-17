# Trident multi-region deployment

Trident uses one codebase and two delivery regions. The application behavior,
database schema, AI orchestration, and report logic remain identical in both
regions.

## Public endpoints

| Audience | Frontend | API | Database |
| --- | --- | --- | --- |
| International | Vercel Next.js | Vercel FastAPI | Neon PostgreSQL |
| Mainland China | Tencent Cloud + EdgeOne | Tencent Cloud container | TencentDB for PostgreSQL |

The Vercel deployment remains the international service. It must not be used
as the only entry point for mainland customers because Vercel does not operate
mainland China infrastructure and cannot guarantee `.vercel.app` availability.

## Mainland production prerequisites

1. A company-owned domain, such as `trident.example.com`.
2. A mainland China cloud account with real-name verification.
3. An ICP filing for the mainland-facing hostname.
4. TencentDB for PostgreSQL and a least-privilege application user.
5. A Tencent Cloud CVM or container service reachable by EdgeOne.
6. EdgeOne mainland acceleration, TLS, WAF, and origin protection.

The application continues to use the standard `DATABASE_URL` contract. Moving
from Neon to TencentDB therefore changes deployment configuration, not business
code or persistence models.

## Mainland deployment

The production-ready container baseline is in [`deploy/china`](deploy/china).
It runs the existing Next.js and FastAPI applications behind a single Nginx
origin and is designed for EdgeOne to terminate TLS and accelerate the custom
domain.

```bash
cd deploy/china
cp .env.example .env
# Fill real DATABASE_URL and provider credentials in .env.
docker compose up -d --build
```

Do not commit `.env`. Verify the origin before attaching the domain:

```bash
python ../../scripts/smoke_deployment.py \
  --web-url https://cn.example.com \
  --api-url https://cn.example.com/platform-api
```

## Traffic design

- `app.example.com` routes international users to Vercel.
- `cn.example.com` routes mainland users to Tencent Cloud through EdgeOne.
- A later GeoDNS layer may route one branded hostname by geography, but two
  explicit hostnames are easier to validate and support during launch.
- Browsers call only the regional Trident origin. Model and search credentials
  stay server-side; browsers never call HKGAI or the search service directly.

## Availability safeguards

- `/healthz` checks the China web origin.
- `/platform-api/health` checks the API process.
- `/platform-api/ready` checks API plus PostgreSQL readiness.
- EdgeOne origin health checks should use `/healthz`.
- External monitoring should probe all three paths from mainland provinces.
- Keep daily TencentDB backups and test restore procedures before onboarding
  customer data.

## International deployment

The existing Vercel projects continue to deploy from `main`:

- Frontend: `trident-research.vercel.app`
- API: `trident-research-api.vercel.app`

Their secrets remain in Vercel environment settings and are never committed.
The international deployment is independent of the original Streamlit app.

## Release rule

Every release must pass the same tests once, build the same immutable images,
and then promote those images to both regions. Region-specific branches or
copied application code are not allowed.
