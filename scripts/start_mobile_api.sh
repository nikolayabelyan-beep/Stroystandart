#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/nikolajtamrazov/Documents/BACKUP_GOLD"
PYTHON_BIN="$(xcrun --find python3 || command -v python3)"
LOG_DIR="$ROOT_DIR/data/mobile_api"
mkdir -p "$LOG_DIR"

exec "$PYTHON_BIN" "$ROOT_DIR/src/api/mobile_control_server.py" --host 0.0.0.0 --port 8787 \
  >>"$LOG_DIR/server.log" 2>&1
