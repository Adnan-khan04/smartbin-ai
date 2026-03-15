#!/usr/bin/env bash
# Start both backend and frontend in background (Unix / WSL / Git Bash)
# - Uses backend/venv python to run main.py and npm run dev in frontend
# - Logs are written to /tmp for convenience

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend/smartbin-ai"
PYTHON_EXE="$BACKEND_DIR/venv/Scripts/python.exe"

echo "Starting backend -> $BACKEND_DIR"
"$PYTHON_EXE" "$BACKEND_DIR/main.py" > /tmp/smartbin-backend.log 2>&1 &
BACKEND_PID=$!

echo "Starting frontend -> $FRONTEND_DIR"
( cd "$FRONTEND_DIR" && npm run dev > /tmp/smartbin-frontend.log 2>&1 & )
FRONTEND_PID=$!

sleep 1

echo "Backend PID: $BACKEND_PID (logs: /tmp/smartbin-backend.log)"
echo "Frontend PID: $FRONTEND_PID (logs: /tmp/smartbin-frontend.log)"

echo "To stop: kill $BACKEND_PID $FRONTEND_PID"