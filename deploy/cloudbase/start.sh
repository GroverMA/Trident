#!/bin/sh
set -eu

export TRIDENT_API_URL="http://127.0.0.1:8000"

python -m alembic upgrade head
python -m uvicorn api:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers "${WEB_CONCURRENCY:-1}" \
  --proxy-headers &
api_pid=$!

cleanup() {
  kill "$api_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd /app/cloudbase-web
HOSTNAME=0.0.0.0 PORT="${PORT:-3000}" node server.js
