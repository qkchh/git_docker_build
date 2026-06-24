#!/usr/bin/env bash
set -e

PORT=3002
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="$SCRIPT_DIR/data/app.log"
PID_FILE="$SCRIPT_DIR/data/app.pid"

mkdir -p "$SCRIPT_DIR/data"

# ── Detect python ─────────────────────────────────────
if command -v python3 &>/dev/null; then
  PYTHON=python3
elif command -v python &>/dev/null; then
  PYTHON=python
else
  echo "ERROR: python3 / python not found. Please install Python 3.12+."
  exit 1
fi

PY_VER=$($PYTHON -c "import sys; print(sys.version_info.major)")
if [ "$PY_VER" -lt 3 ]; then
  echo "ERROR: Python 3 is required, but '$PYTHON' is Python $PY_VER."
  exit 1
fi

echo "Using $($PYTHON --version)"

# ── Create venv if not exists ─────────────────────────
if [ ! -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
  echo "Creating virtual environment..."
  $PYTHON -m venv .venv
fi

# ── Activate venv ─────────────────────────────────────
source "$SCRIPT_DIR/.venv/bin/activate"

# ── Install / update dependencies ─────────────────────
echo "Installing dependencies..."
pip install -q --no-cache-dir -r requirements.txt
echo "Dependencies ready."

# ── Kill anything on port $PORT ───────────────────────
EXISTING=$(lsof -ti tcp:$PORT 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
  echo "Port $PORT in use (pid $EXISTING), killing..."
  kill -9 $EXISTING 2>/dev/null || true
  sleep 0.5
fi
rm -f "$PID_FILE"

# ── Start in background ───────────────────────────────
echo "Starting service..."
: > "$LOG_FILE"   # truncate log
PYTHONUNBUFFERED=1 nohup uvicorn main:app --host 0.0.0.0 --port $PORT >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

# ── Wait for startup (max 30s, poll every 1s) ─────────
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
