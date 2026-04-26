#!/usr/bin/env bash
set -euo pipefail

MODE="${SERVICE_MODE:-api}"

mkdir -p /app/data/runtime /app/data/director_uploads /app/output

case "$MODE" in
  api)
    exec python /app/src/api/mobile_control_server.py --host 0.0.0.0 --port 8787
    ;;
  bot)
    exec python -m src.bot.telegram_app
    ;;
  *)
    echo "Unknown SERVICE_MODE: $MODE" >&2
    exit 1
    ;;
esac
