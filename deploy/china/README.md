# Mainland China deployment baseline

This directory deploys the existing Trident web and API code without a fork.
It is intended for a Tencent Cloud origin protected and accelerated by EdgeOne.

## Topology

```text
Mainland browser -> ICP-filed domain -> EdgeOne -> Nginx
    -> Next.js web
    -> FastAPI -> TencentDB for PostgreSQL
               -> server-side model and search providers
```

## Provisioning checklist

1. Create TencentDB for PostgreSQL in the same region as compute.
2. Restrict its security group to the Trident API origin.
3. Create a CVM with Docker Engine and the Compose plugin.
4. Copy `.env.example` to `.env` and enter production secrets.
5. Run `docker compose up -d --build`.
6. Confirm `/healthz`, `/platform-api/health`, and `/platform-api/ready`.
7. Add the ICP-filed hostname to EdgeOne using `/healthz` for origin checks.
8. Enable TLS, WAF, rate limits, access logs, and alerting.
9. Test China Mobile, China Unicom, and China Telecom before customer launch.

Customer project data must use the configured regional PostgreSQL service.
Calls to model and search providers originate from FastAPI, so credentials are
not exposed to browsers. Confirm legal requirements before sending customer
data to any external model provider.

Use versioned image tags in production and keep the last known-good tags for
rollback. Database migrations must remain backward compatible for one release.
