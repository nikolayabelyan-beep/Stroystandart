#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/nikolajtamrazov/Documents/BACKUP_GOLD"
LOG_DIR="$ROOT/data/runtime"
mkdir -p "$LOG_DIR"

cd "$ROOT"

while true; do
  python3 src/api/mobile_control_server.py --host 0.0.0.0 --port 8787 >>"$LOG_DIR/mobile_api.log" 2>&1 || true
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] api exited, restart in 3s" >>"$LOG_DIR/mobile_api.log"
  sleep 3
done
