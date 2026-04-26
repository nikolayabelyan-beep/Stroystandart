# StroyStandart Cloud Deployment

Этот пакет нужен, чтобы система работала, даже когда Mac выключен.

## Что поднимается

- `api` — мобильный API для iPhone и логика директора
- `bot` — Telegram-бот
- `caddy` — HTTPS reverse proxy с автоматическим TLS

## Что нужно заранее

1. Linux VPS с публичным IP
2. Домен, направленный на VPS
3. Docker и Docker Compose plugin
4. Скопированный проект на сервер, например в `/opt/stroystandart`

## Подготовка сервера

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo mkdir -p /opt/stroystandart
sudo chown -R $USER:$USER /opt/stroystandart
```

Или быстрым способом:

```bash
curl -fsSL https://raw.githubusercontent.com/nikolayabelyan-beep/Stroystandart/main/deploy/cloud/bootstrap_vps.sh -o bootstrap_vps.sh
bash bootstrap_vps.sh
```

## Загрузка проекта

```bash
git clone https://github.com/nikolayabelyan-beep/Stroystandart.git /opt/stroystandart
cd /opt/stroystandart
cp .env.cloud.example .env.cloud
```

Заполни `.env.cloud`:

- `APP_DOMAIN`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Запуск

```bash
cd /opt/stroystandart
docker compose -f deploy/cloud/docker-compose.cloud.yml up -d --build
```

## Проверка

```bash
docker compose -f deploy/cloud/docker-compose.cloud.yml ps
curl https://YOUR_DOMAIN/health
```

Ожидаемый ответ:

```json
{"ok": true, "service": "mobile_control_server"}
```

## Автозапуск после перезагрузки VPS

```bash
sudo cp deploy/cloud/stroystandart-cloud.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now stroystandart-cloud.service
```

## Важно про iPhone приложение

После запуска в облаке API URL в приложении должен быть таким:

```text
https://YOUR_DOMAIN
```

Локальный адрес Mac больше не нужен.

## Что меняется в облачном режиме

- `CLOUD_MODE=1`
- API не пытается запускать локальные `launchd`/Mac scripts
- `services/status` возвращает cloud-managed статус
- бот и API перезапускаются контейнерным рантаймом

## Обновление версии

```bash
cd /opt/stroystandart
git pull
docker compose -f deploy/cloud/docker-compose.cloud.yml up -d --build
```

## Логи

```bash
docker compose -f deploy/cloud/docker-compose.cloud.yml logs -f api
docker compose -f deploy/cloud/docker-compose.cloud.yml logs -f bot
docker compose -f deploy/cloud/docker-compose.cloud.yml logs -f caddy
```
