#!/usr/bin/env bash
set -euo pipefail

pkill -f "[r]un_api_supervisor.sh" >/dev/null 2>&1 || true
pkill -f "mobile_control_server.py --host 0.0.0.0 --port 8787" >/dev/null 2>&1 || true
pkill -f "[r]un_bot_supervisor.sh" >/dev/null 2>&1 || true
pkill -f "src.bot.telegram_app" >/dev/null 2>&1 || true

echo "[OK] Services stopped"
