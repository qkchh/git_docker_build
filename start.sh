#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="$SCRIPT_DIR/data/app.log"
PID_FILE="$SCRIPT_DIR/data/app.pid"

mkdir -p "$SCRIPT_DIR/data"

# ── Check if already running ───────────────────────────
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Already running (pid $OLD_PID). Use ./stop.sh to stop it first."
    exit 1
  else
    rm -f "$PID_FILE"
  fi
fi

# ── Activate venv if present ──────────────────────────
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
  source "$SCRIPT_DIR/.venv/bin/activate"
fi

# ── Start in background ───────────────────────────────
nohup uvicorn main:app --host 0.0.0.0 --port 3002 >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "Started (pid $(cat "$PID_FILE"))"
echo "Log:  $LOG_FILE"

# ── Wait a moment then print the access token ─────────
sleep 1
echo ""
grep -m1 "Access Token" "$LOG_FILE" || true
