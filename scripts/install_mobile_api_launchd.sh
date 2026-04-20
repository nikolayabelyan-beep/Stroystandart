#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/nikolajtamrazov/Documents/BACKUP_GOLD"
PLIST_PATH="$HOME/Library/LaunchAgents/com.stroystandart.mobileapi.plist"
START_SCRIPT="$ROOT_DIR/scripts/start_mobile_api.sh"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$ROOT_DIR/data/mobile_api"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.stroystandart.mobileapi</string>

    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>$START_SCRIPT</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>WorkingDirectory</key>
    <string>$ROOT_DIR</string>

    <key>StandardOutPath</key>
    <string>$ROOT_DIR/data/mobile_api/launchd.out.log</string>

    <key>StandardErrorPath</key>
    <string>$ROOT_DIR/data/mobile_api/launchd.err.log</string>
  </dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/com.stroystandart.mobileapi" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/com.stroystandart.mobileapi"

echo "[OK] Installed and started: com.stroystandart.mobileapi"
echo "[OK] Plist: $PLIST_PATH"
