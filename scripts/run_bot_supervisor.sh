#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/nikolajtamrazov/Documents/BACKUP_GOLD"
LOG_DIR="$ROOT/data/runtime"
mkdir -p "$LOG_DIR"

cd "$ROOT"

while true; do
  HTTPS_PROXY= HTTP_PROXY= ALL_PROXY= NO_PROXY='*' python3 -m src.bot.telegram_app >>"$LOG_DIR/telegram_bot.log" 2>&1 || true
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] bot exited, restart in 5s" >>"$LOG_DIR/telegram_bot.log"
  sleep 5
done
