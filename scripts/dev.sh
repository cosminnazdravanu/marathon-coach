#!/usr/bin/env bash
set -euo pipefail

# backend
( source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
  python -m uvicorn backend.main:app --reload
) &
BACK_PID=$!

# frontend
( cd frontend && npm run dev -- --host 127.0.0.1 ) &
FRONT_PID=$!

# cleanup on exit
trap 'echo; echo "Shutting down..."; kill $BACK_PID $FRONT_PID 2>/dev/null || true' INT TERM
wait
