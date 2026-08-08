#!/usr/bin/env python3
"""
Автономный запуск оркестратора ИИ-офиса

Оркестратор работает 24/7 и отправляет:
- Утренний план задач в 08:00
- Вечерний отчет о выполненном в 18:00
- Мгновенные alert при HIGH рисках (>=7)
"""

import asyncio
import sys
import logging
from datetime import datetime, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.orchestrator import AIOrchestrator
from src.core.notification_service import NotificationService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/orchestrator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('OrchestratorRunner')


async def main():
    """Основной цикл работы оркестратора"""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК АВТОНОМНОГО ОРКЕСТРАТОРА ИИ-ОФИСА")
    logger.info("=" * 60)
    
    orch = AIOrchestrator()
    notif = orch.notification_service
    
    # Отправляем сообщение о запуске
    await notif.send_telegram_message(
        "🚀 <b>Оркестратор запущен!</b>\n\n"
        "Режим работы: автономный\n"
        "📅 Утренний план: 08:00\n"
        "📊 Вечерний отчет: 18:00\n"
        "⚠️ HIGH риски: мгновенно\n\n"
        "Все агенты готовы к работе."
    )
    
    logger.info("Оркестратор запущен. Ожидание задач...")
    
    # Основной цикл (в реальной реализации здесь будет обработка очереди задач)
    while True:
        now = datetime.now()
        
        # Проверка времени для утреннего плана
        if now.hour == 8 and now.minute == 0:
            logger.info("Генерация утреннего плана...")
            await orch._send_morning_plan()
            await asyncio.sleep(60)  # Ждем минуту чтобы не сработало повторно
        
        # Проверка времени для вечернего отчета
        elif now.hour == 18 and now.minute == 0:
            logger.info("Генерация вечернего отчета...")
            await orch._send_evening_report()
            await asyncio.sleep(60)
        
        # Здесь будет обработка входящих задач из очереди
        # await orch._process_task_queue()
        
        await asyncio.sleep(30)  # Проверка каждые 30 секунд


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Оркестратор остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
