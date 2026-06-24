#!/usr/bin/env bash
set -e

PORT=3002
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="$SCRIPT_DIR/data/app.log"
PID_FILE="$SCRIPT_DIR/data/app.pid"

mkdir -p "$SCRIPT_DIR/data"

# ── Kill anything on port 3002 ────────────────────────
EXISTING=$(lsof -ti tcp:$PORT 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
  echo "Port $PORT in use (pid $EXISTING), killing..."
  kill -9 $EXISTING 2>/dev/null || true
  sleep 0.5
fi
rm -f "$PID_FILE"

# ── Activate venv if present ──────────────────────────
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
  source "$SCRIPT_DIR/.venv/bin/activate"
fi

# ── Start in background ───────────────────────────────
: > "$LOG_FILE"   # truncate log
PYTHONUNBUFFERED=1 nohup uvicorn main:app --host 0.0.0.0 --port $PORT >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

# ── Wait for startup (max 30s, poll every 1s) ─────────
echo "Waiting for service to start..."
MAX=30
COUNT=0
while [ $COUNT -lt $MAX ]; do
  sleep 1
  COUNT=$((COUNT + 1))
  if grep -q "Access Token" "$LOG_FILE" 2>/dev/null; then
    break
  fi
done

if ! grep -q "Access Token" "$LOG_FILE" 2>/dev/null; then
  echo "ERROR: Service did not start within 30 seconds. Check $LOG_FILE"
  exit 1
fi

# ── Print address & token ─────────────────────────────
TOKEN=$(grep -m1 "Access Token" "$LOG_FILE" | sed 's/.*Access Token: //' | tr -d '[:space:]')

echo ""
echo "=================================================="
echo "  URL:    http://localhost:$PORT"
echo "  Token:  $TOKEN"
echo "=================================================="
echo ""
