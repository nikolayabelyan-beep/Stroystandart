#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="$HOME/StroyStandartRuntime"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
RUNTIME_DIR="$RUNTIME_ROOT/data/runtime"

API_LABEL="com.stroystandart.api-supervisor"
BOT_LABEL="com.stroystandart.bot-supervisor"
WATCHDOG_LABEL="com.stroystandart.service-watchdog"

API_PLIST="$LAUNCH_AGENTS_DIR/${API_LABEL}.plist"
BOT_PLIST="$LAUNCH_AGENTS_DIR/${BOT_LABEL}.plist"
WATCHDOG_PLIST="$LAUNCH_AGENTS_DIR/${WATCHDOG_LABEL}.plist"

mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$RUNTIME_DIR"

# macOS launchd may be denied access to ~/Documents by TCC.
# Keep an executable runtime copy outside protected folders.
rsync -a --delete \
  --exclude ".git/" \
  --exclude "ios/" \
  --exclude "output/" \
  --exclude "DerivedData/" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  "$ROOT_DIR/" "$RUNTIME_ROOT/"

cat > "$API_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>$API_LABEL</string>

    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>$RUNTIME_ROOT/scripts/run_api_supervisor.sh</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$RUNTIME_ROOT</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>StandardOutPath</key>
    <string>$RUNTIME_DIR/launchd_api.out.log</string>

    <key>StandardErrorPath</key>
    <string>$RUNTIME_DIR/launchd_api.err.log</string>
  </dict>
</plist>
PLIST

cat > "$BOT_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>$BOT_LABEL</string>

    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>$RUNTIME_ROOT/scripts/run_bot_supervisor.sh</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$RUNTIME_ROOT</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
      <key>HTTPS_PROXY</key>
      <string></string>
      <key>HTTP_PROXY</key>
      <string></string>
      <key>ALL_PROXY</key>
      <string></string>
      <key>NO_PROXY</key>
      <string>*</string>
    </dict>

    <key>StandardOutPath</key>
    <string>$RUNTIME_DIR/launchd_bot.out.log</string>

    <key>StandardErrorPath</key>
    <string>$RUNTIME_DIR/launchd_bot.err.log</string>
  </dict>
</plist>
PLIST

cat > "$WATCHDOG_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>$WATCHDOG_LABEL</string>

    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>$RUNTIME_ROOT/scripts/run_service_watchdog.sh</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$RUNTIME_ROOT</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
      <key>HTTPS_PROXY</key>
      <string></string>
      <key>HTTP_PROXY</key>
      <string></string>
      <key>ALL_PROXY</key>
      <string></string>
      <key>NO_PROXY</key>
      <string>*</string>
    </dict>

    <key>StandardOutPath</key>
    <string>$RUNTIME_DIR/launchd_watchdog.out.log</string>

    <key>StandardErrorPath</key>
    <string>$RUNTIME_DIR/launchd_watchdog.err.log</string>
  </dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/$API_LABEL" >/dev/null 2>&1 || true
launchctl bootout "gui/$(id -u)/$BOT_LABEL" >/dev/null 2>&1 || true
launchctl bootout "gui/$(id -u)/$WATCHDOG_LABEL" >/dev/null 2>&1 || true

launchctl bootstrap "gui/$(id -u)" "$API_PLIST"
launchctl bootstrap "gui/$(id -u)" "$BOT_PLIST"
launchctl bootstrap "gui/$(id -u)" "$WATCHDOG_PLIST"

launchctl kickstart -k "gui/$(id -u)/$API_LABEL"
launchctl kickstart -k "gui/$(id -u)/$BOT_LABEL"
launchctl kickstart -k "gui/$(id -u)/$WATCHDOG_LABEL"

echo "[OK] launchd installed and started:"
echo "  - $API_LABEL"
echo "  - $BOT_LABEL"
echo "  - $WATCHDOG_LABEL"
echo "[OK] Runtime copy:"
echo "  - $RUNTIME_ROOT"
echo "[OK] Plists:"
echo "  - $API_PLIST"
echo "  - $BOT_PLIST"
echo "  - $WATCHDOG_PLIST"
