#!/usr/bin/env python3
"""
Точка входа для Telegram бота ИИ-офиса.
Рабочая среда без заглушек.
"""

import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent))

# Проверка переменных окружения
if not os.getenv("TELEGRAM_BOT_TOKEN"):
    print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    print("Установите: export TELEGRAM_BOT_TOKEN='your_token_here'")
    sys.exit(1)

if not os.getenv("DEEPSEEK_API_KEY"):
    print("⚠️  WARNING: DEEPSEEK_API_KEY не найден, бот будет работать без AI")

# Запускаем бота
from src.bot.telegram_app import main

if __name__ == '__main__':
    main()
