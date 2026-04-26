# Hetzner + Cloudflare Auto Provisioning

Этот пакет автоматически:

- создает VPS в `Hetzner Cloud`
- добавляет `SSH key`
- открывает `22/80/443`
- создает DNS запись в `Cloudflare`
- выполняет начальный bootstrap сервера

## Что нужно от тебя

1. `Hetzner Cloud API token`
2. `Cloudflare API token`
3. `Cloudflare Zone ID`
4. публичный `SSH key`

## Подготовка локально

Установи Terraform:

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

Создай SSH ключ, если еще нет:

```bash
ssh-keygen -t ed25519 -C "stroystandart-cloud" -f ~/.ssh/stroystandart_cloud
cat ~/.ssh/stroystandart_cloud.pub
```

## Настройка

```bash
cd /Users/nikolajtamrazov/Documents/BACKUP_GOLD/deploy/terraform-hetzner-cloudflare
cp terraform.tfvars.example terraform.tfvars
```

Заполни `terraform.tfvars`.

## Запуск

```bash
terraform init
terraform plan
terraform apply
```

## Что получишь

Terraform выведет:

- `server_ip`
- `office_domain`
- `ssh_command`
- `app_url`

## После создания сервера

Подключись:

```bash
ssh root@SERVER_IP
```

Потом:

```bash
cd /opt/stroystandart
nano .env.cloud
```

Заполни:

- `APP_DOMAIN`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Потом старт:

```bash
docker compose -f deploy/cloud/docker-compose.cloud.yml up -d --build
```

## Проверка

```bash
curl https://office.example.com/health
```

## Удаление

```bash
terraform destroy
```
