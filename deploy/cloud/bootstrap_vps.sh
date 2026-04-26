#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/stroystandart}"
REPO_URL="${REPO_URL:-https://github.com/nikolayabelyan-beep/Stroystandart.git}"

sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker

if [ ! -d "$APP_DIR/.git" ]; then
  sudo mkdir -p "$APP_DIR"
  sudo chown -R "$USER:$USER" "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

if [ ! -f .env.cloud ]; then
  cp .env.cloud.example .env.cloud
  echo "Created .env.cloud from template. Fill secrets before first start."
fi

chmod +x deploy/cloud/entrypoint.sh

echo "Bootstrap completed."
echo "Next steps:"
echo "1. Edit $APP_DIR/.env.cloud"
echo "2. Run: docker compose -f deploy/cloud/docker-compose.cloud.yml up -d --build"
