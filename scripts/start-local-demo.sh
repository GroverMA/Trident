#!/bin/zsh
set -euo pipefail

script_dir=${0:A:h}
repo_root=${script_dir:h}

if [[ ! -x "${repo_root}/.venv/bin/python" ]]; then
  print -u2 "Missing ${repo_root}/.venv. Create the Python environment before starting Trident."
  exit 1
fi

cleanup() {
  [[ -n "${api_pid:-}" ]] && kill "${api_pid}" 2>/dev/null || true
  [[ -n "${web_pid:-}" ]] && kill "${web_pid}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "${repo_root}"
TRIDENT_ENV=development .venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8000 &
api_pid=$!

cd "${repo_root}/web"
pnpm dev --hostname 127.0.0.1 &
web_pid=$!

print "Trident local demo: http://127.0.0.1:3000"
print "Web and research API are running together. Press Ctrl+C to stop both."
wait
