#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/data/runtime"
LOG_FILE="$LOG_DIR/service_watchdog.log"
mkdir -p "$LOG_DIR"

API_LABEL="com.stroystandart.api-supervisor"
BOT_LABEL="com.stroystandart.bot-supervisor"

check_http() {
  local url="$1"
  curl -fsS --max-time 4 "$url" >/dev/null 2>&1
}

kick_label() {
  local label="$1"
  launchctl kickstart -k "gui/$(id -u)/$label" >/dev/null 2>&1 || true
}

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >>"$LOG_FILE"
}

fail_count=0
ok_ticks=0
log "watchdog started (root=$ROOT)"

while true; do
  ok=true

  if ! pgrep -f "[r]un_api_supervisor.sh" >/dev/null 2>&1; then
    ok=false
  fi
  if ! pgrep -f "[r]un_bot_supervisor.sh" >/dev/null 2>&1; then
    ok=false
  fi
  if ! check_http "http://127.0.0.1:8787/health"; then
    ok=false
  fi
  if ! check_http "http://127.0.0.1:8787/director/history"; then
    ok=false
  fi

  if $ok; then
    fail_count=0
    ok_ticks=$((ok_ticks + 1))
    if (( ok_ticks % 30 == 0 )); then
      log "healthy"
    fi
  else
    fail_count=$((fail_count + 1))
    log "check failed (consecutive=$fail_count), restarting supervisors"
    kick_label "$API_LABEL"
    kick_label "$BOT_LABEL"
    sleep 3
    if (( fail_count >= 4 )); then
      log "hard restart fallback via scripts/start_services.sh"
      /bin/bash "$ROOT/scripts/start_services.sh" >>"$LOG_FILE" 2>&1 || true
      fail_count=0
    fi
  fi

  sleep 20
done
