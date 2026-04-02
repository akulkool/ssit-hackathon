#!/usr/bin/env bash
# FinSight AI — start API + Vite dev server (macOS-friendly).
# Usage: from FinSightAI/: chmod +x run.sh && ./run.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

BACK_PID=""
FRONT_PID=""

cleanup() {
  if [[ -n "${BACK_PID}" ]] && kill -0 "$BACK_PID" 2>/dev/null; then
    kill "$BACK_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONT_PID}" ]] && kill -0 "$FRONT_PID" 2>/dev/null; then
    kill "$FRONT_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

# Backend: prefer backend/.venv
PY=""
if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  PY="$ROOT/backend/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  echo "Need python3 or backend/.venv (create: cd backend && python3 -m venv .venv && pip install -r requirements.txt)" >&2
  exit 1
fi

(
  cd "$ROOT/backend"
  export UVICORN_RELOAD=1
  exec "$PY" app.py
) &
BACK_PID=$!

(
  cd "$ROOT/frontend"
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  exec npm run dev
) &
FRONT_PID=$!

echo "FinSight: API (pid $BACK_PID) + Vite (pid $FRONT_PID)"
echo "  API:    http://127.0.0.1:8000/health"
echo "  App:    http://localhost:5173"

sleep 2
if command -v open >/dev/null 2>&1; then
  open "http://localhost:5173" || true
fi

wait "$BACK_PID" "$FRONT_PID"
