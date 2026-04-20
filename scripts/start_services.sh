#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/nikolajtamrazov/Documents/BACKUP_GOLD"
LOG_DIR="$ROOT/data/runtime"
API_LOG="$LOG_DIR/mobile_api.log"
BOT_LOG="$LOG_DIR/telegram_bot.log"

mkdir -p "$LOG_DIR"
cd "$ROOT"

# Ensure required runtime deps for bot are present.
python3 - <<'PY'
import importlib.util, subprocess, sys
required = ["telegram", "dotenv"]
missing = [m for m in required if importlib.util.find_spec(m) is None]
if missing:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "python-telegram-bot[socks]==21.6", "python-dotenv"])
PY

# Start API supervisor if not running.
if ! pgrep -f "[r]un_api_supervisor.sh" >/dev/null 2>&1; then
  nohup "$ROOT/scripts/run_api_supervisor.sh" >>"$API_LOG" 2>&1 &
  echo $! > "$LOG_DIR/mobile_api.pid"
fi

# Start Telegram bot supervisor if not running.
if ! pgrep -f "[r]un_bot_supervisor.sh" >/dev/null 2>&1; then
  nohup "$ROOT/scripts/run_bot_supervisor.sh" >>"$BOT_LOG" 2>&1 &
  echo $! > "$LOG_DIR/telegram_bot.pid"
fi

# Wait a moment for API bootstrap and run health checks
sleep 2
python3 - <<'PY'
import urllib.request
for u in ("http://127.0.0.1:8787/health", "http://192.168.0.107:8787/health"):
    try:
        print(u, urllib.request.urlopen(u, timeout=4).status)
    except Exception as e:
        print(u, f"ERR: {e}")
PY

pgrep -fal "run_api_supervisor.sh|mobile_control_server.py --host 0.0.0.0 --port 8787|run_bot_supervisor.sh|src.bot.telegram_app" || true

echo "[OK] Services start attempted. Logs: $LOG_DIR"
