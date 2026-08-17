FROM node:22-bookworm-slim AS web-dependencies
WORKDIR /build/web
RUN corepack enable
COPY web/package.json web/pnpm-lock.yaml web/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:22-bookworm-slim AS web-builder
WORKDIR /build/web
RUN corepack enable
COPY --from=web-dependencies /build/web/node_modules ./node_modules
COPY web/ ./
ENV TRIDENT_API_URL=http://127.0.0.1:8000
RUN pnpm build

FROM node:22-bookworm-slim AS node-runtime

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRIDENT_ENV=production \
    TRIDENT_API_URL=http://127.0.0.1:8000 \
    PORT=3000

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=web-builder /build/web/.next/standalone ./cloudbase-web
COPY --from=web-builder /build/web/.next/static ./cloudbase-web/.next/static
COPY deploy/cloudbase/start.sh /app/deploy/cloudbase/start.sh

EXPOSE 3000
CMD ["/bin/sh", "/app/deploy/cloudbase/start.sh"]
