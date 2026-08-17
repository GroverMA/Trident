#!/bin/sh
set -eu

export TRIDENT_API_URL="http://127.0.0.1:8000"
export TRIDENT_DATABASE_PATH="${TRIDENT_DATABASE_PATH:-/app/data/trident.db}"
export WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"

mkdir -p "$(dirname "$TRIDENT_DATABASE_PATH")"
PORT=8000 python scripts/start_api.py &
api_pid=$!

cleanup() {
  kill "$api_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd /app/cloudbase-web
HOSTNAME=0.0.0.0 PORT=3000 node server.js
