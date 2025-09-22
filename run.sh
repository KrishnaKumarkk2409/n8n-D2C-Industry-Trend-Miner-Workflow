#!/usr/bin/env bash
# run.sh — free :8000, then start uvicorn main:app --reload in ./env
set -euo pipefail

# --- Config ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${BASE_DIR:-$SCRIPT_DIR}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
MODULE="${MODULE:-app:app}"      # use app:app as requested
VENV="${VENV:-$BASE_DIR/env}"     # virtualenv path
LOGDIR="${LOGDIR:-$BASE_DIR/logs}"
PIDFILE="$BASE_DIR/.uvicorn.$PORT.pid"
LOGFILE="$LOGDIR/uvicorn_$PORT.log"

mkdir -p "$LOGDIR"
cd "$BASE_DIR"

# --- venv ---
if [[ -f "$VENV/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
else
  echo "venv missing: $VENV"
  echo "Create: python3 -m venv \"$VENV\" && source \"$VENV/bin/activate\" && pip install fastapi uvicorn 'httpx[http2]' feedparser beautifulsoup4 watchfiles"
  exit 1
fi

pids_on_port() { lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true; }

hard_nuke() {
  # Kill anything likely to hold :$PORT or reload it
  pkill -f "uvicorn .*${MODULE}.*--port ${PORT}" 2>/dev/null || true
  pkill -f "watchfiles .*${MODULE}" 2>/dev/null || true
  pkill -f "python .*${MODULE}" 2>/dev/null || true
}

free_port() {
  local pids
  pids="$(pids_on_port)"
  if [[ -n "${pids:-}" ]]; then
    echo "TERM on :$PORT → $pids"
    kill -TERM $pids 2>/dev/null || true
  fi
  # Wait up to 5s
  for _ in {1..20}; do
    sleep 0.25
    pids="$(pids_on_port)"
    [[ -z "${pids:-}" ]] && break
  done
  # If still busy, KILL and nuke matching processes
  pids="$(pids_on_port)"
  if [[ -n "${pids:-}" ]]; then
    echo "KILL on :$PORT → $pids"
    kill -KILL $pids 2>/dev/null || true
  fi
  hard_nuke
  # Final wait until truly free (max ~5s)
  for _ in {1..20}; do
    sleep 0.25
    [[ -z "$(pids_on_port)" ]] && return 0
  done
  echo "Error: port $PORT still busy"; exit 1
}

deps() {
  python -m pip install --upgrade pip >/dev/null 2>&1 || true
  python -m pip install fastapi uvicorn 'httpx[http2]' feedparser beautifulsoup4 watchfiles
}

start() {
  rm -f "$PIDFILE"
  free_port
  echo "Starting uvicorn $MODULE on $HOST:$PORT (reload)"
  nohup uvicorn "$MODULE" --host "$HOST" --port "$PORT" --reload >>"$LOGFILE" 2>&1 &
  echo $! > "$PIDFILE"
  disown || true
  echo "PID $(cat "$PIDFILE") • logs: $LOGFILE"
}

start_fg() {
  rm -f "$PIDFILE"
  free_port
  exec uvicorn "$MODULE" --host "$HOST" --port "$PORT" --reload
}

stop() {
  local pids
  pids="$(pids_on_port)"
  if [[ -n "${pids:-}" ]]; then
    echo "Stopping :$PORT → $pids"
    kill -TERM $pids 2>/dev/null || true
  fi
  sleep 0.5
  pids="$(pids_on_port)"
  if [[ -n "${pids:-}" ]]; then
    echo "Force kill :$PORT → $pids"
    kill -KILL $pids 2>/dev/null || true
  fi
  hard_nuke
  rm -f "$PIDFILE"
  echo "Stopped."
}

status() {
  local pids; pids="$(pids_on_port)"
  if [[ -n "${pids:-}" ]]; then
    echo "Listening on :$PORT (pids: $pids)"
  else
    echo "Not listening on :$PORT"
  fi
}

logs() { : > "$LOGFILE"; tail -n 200 -f "$LOGFILE"; }

case "${1:-start}" in
  deps) deps ;;
  start) start ;;
  start-fg) start_fg ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  logs) logs ;;
  *) echo "Usage: $0 {deps|start|start-fg|stop|restart|status|logs}"; exit 2 ;;
esac
