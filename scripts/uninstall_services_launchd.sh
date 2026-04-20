#!/usr/bin/env bash
set -euo pipefail

API_LABEL="com.stroystandart.api-supervisor"
BOT_LABEL="com.stroystandart.bot-supervisor"

API_PLIST="$HOME/Library/LaunchAgents/${API_LABEL}.plist"
BOT_PLIST="$HOME/Library/LaunchAgents/${BOT_LABEL}.plist"

launchctl bootout "gui/$(id -u)/$API_LABEL" >/dev/null 2>&1 || true
launchctl bootout "gui/$(id -u)/$BOT_LABEL" >/dev/null 2>&1 || true

rm -f "$API_PLIST" "$BOT_PLIST"

echo "[OK] launchd removed:"
echo "  - $API_LABEL"
echo "  - $BOT_LABEL"
