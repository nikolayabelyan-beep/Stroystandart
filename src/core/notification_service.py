"""
Notification Service for AI Office
Система уведомлений для ИИ-агентов с интеграцией Telegram
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import aiohttp
import asyncio


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Notification:
    """Сообщение уведомления"""
    notification_id: str
    priority: str
    title: str
    message: str
    recipient: str
    timestamp: str
    metadata: Dict
    requires_acknowledgment: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'notification_id': self.notification_id,
            'priority': self.priority,
            'title': self.title,
            'message': self.message,
            'recipient': self.recipient,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
            'requires_acknowledgment': self.requires_acknowledgment
        }


class NotificationService:
    """
    Сервис уведомлений для ИИ-офиса
    Поддерживает Telegram, email и логирование
    """
    
    def __init__(self, config_path: str = '/workspace/agents_config.yaml'):
        self.config = self._load_config(config_path)
        self.telegram_bot_token = self.config.get('telegram', {}).get('bot_token', '')
        self.telegram_chat_id = self.config.get('telegram', {}).get('chat_id', '')
        self.notifications_log = []
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('NotificationService')
    
    def _load_config(self, config_path: str) -> Dict:
        """Загрузка конфигурации из YAML файла"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить конфиг: {e}. Использую настройки по умолчанию.")
            return {}
    
    async def send_telegram_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Отправка сообщения в Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            self.logger.warning("Telegram credentials не настроены. Пропуск отправки.")
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Сообщение успешно отправлено в Telegram")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Ошибка Telegram API: {error_text}")
                        return False
        except Exception as e:
            self.logger.error(f"Ошибка отправки в Telegram: {e}")
            return False
    
    def create_risk_notification(self, risk_card_data: Dict) -> Notification:
        """Создание уведомления на основе Risk Card"""
        risk_level = risk_card_data.get('risk_level', 'UNKNOWN')
        risk_score = risk_card_data.get('risk_score', 0)
        document_id = risk_card_data.get('document_id', 'UNKNOWN')
        critical_issues = risk_card_data.get('critical_issues', [])
        recommendations = risk_card_data.get('recommendations', [])
        
        # Определение приоритета
        if risk_level == 'HIGH':
            priority = NotificationPriority.CRITICAL
        elif risk_level == 'MEDIUM':
            priority = NotificationPriority.HIGH
        else:
            priority = NotificationPriority.MEDIUM
        
        # Формирование сообщения
        emoji = {'LOW': '✅', 'MEDIUM': '⚠️', 'HIGH': '🔴'}
        title = f"{emoji.get(risk_level, '❓')} РИСК УРОВЕНЬ {risk_level} ({risk_score}/10)"
        
        message_lines = [
            f"<b>{title}</b>",
            "",
            f"📄 Документ: {document_id}",
            f"🕒 Время оценки: {risk_card_data.get('assessment_date', 'N/A')}",
            ""
        ]
        
        if critical_issues:
            message_lines.append("<b>Критические проблемы:</b>")
            for issue in critical_issues[:3]:  # Максимум 3 проблемы
                message_lines.append(f"• {issue}")
            message_lines.append("")
        
        if recommendations:
            message_lines.append("<b>Рекомендации:</b>")
            for rec in recommendations[:3]:  # Максимум 3 рекомендации
                message_lines.append(f"• {rec}")
        
        if risk_card_data.get('precedent_matches'):
            message_lines.append("")
            message_lines.append("<b>Найденные прецеденты:</b>")
            for prec in risk_card_data['precedent_matches'][:2]:
                message_lines.append(f"• {prec}")
        
        message = '\n'.join(message_lines)
        
        notification = Notification(
            notification_id=f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            priority=priority.value,
            title=title,
            message=message,
            recipient='director',  # По умолчанию директору
            timestamp=datetime.now().isoformat(),
            metadata={
                'risk_id': risk_card_data.get('risk_id'),
                'risk_level': risk_level,
                'risk_score': risk_score,
                'document_id': document_id
            },
            requires_acknowledgment=(risk_level in ['HIGH', 'MEDIUM'])
        )
        
        return notification
    
    def create_daily_report(self, tasks_completed: List[Dict], tasks_planned: List[Dict]) -> Notification:
        """Создание ежедневного отчета оркестратора"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        title = f"📊 ЕЖЕДНЕВНЫЙ ОТЧЕТ ОРКЕСТРАТОРА ({today})"
        
        message_lines = [
            f"<b>{title}</b>",
            "",
            "<b>✅ Выполнено за сегодня:</b>"
        ]
        
        for task in tasks_completed[:5]:  # Максимум 5 задач
            status_emoji = '✓' if task.get('success', False) else '✗'
            message_lines.append(f"{status_emoji} {task.get('task_name', 'Unknown')}")
            if task.get('details'):
                message_lines.append(f"   └─ {task['details']}")
        
        if len(tasks_completed) > 5:
            message_lines.append(f"... и еще {len(tasks_completed) - 5} задач")
        
        message_lines.append("")
        message_lines.append("<b>📋 План на завтра:</b>")
        
        for task in tasks_planned[:5]:  # Максимум 5 задач
            priority_marker = '🔴' if task.get('priority') == 'HIGH' else '⚪'
            message_lines.append(f"{priority_marker} {task.get('task_name', 'Unknown')}")
        
        if len(tasks_planned) > 5:
            message_lines.append(f"... и еще {len(tasks_planned) - 5} задач")
        
        message_lines.append("")
        message_lines.append("<i>Отчет сгенерирован автоматически AI Orchestrator</i>")
        
        message = '\n'.join(message_lines)
        
        notification = Notification(
            notification_id=f"DAILY-{today}",
            priority=NotificationPriority.MEDIUM.value,
            title=title,
            message=message,
            recipient='director',
            timestamp=datetime.now().isoformat(),
            metadata={
                'report_type': 'daily_summary',
                'tasks_completed_count': len(tasks_completed),
                'tasks_planned_count': len(tasks_planned)
            },
            requires_acknowledgment=False
        )
        
        return notification
    
    def create_morning_plan(self, tasks_planned: List[Dict]) -> Notification:
        """Создание утреннего плана задач"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        title = f"🌅 ПЛАН НА ДЕНЬ ({today})"
        
        message_lines = [
            f"<b>{title}</b>",
            "",
            "<b>Приоритетные задачи:</b>"
        ]
        
        # Сортировка по приоритету
        sorted_tasks = sorted(tasks_planned, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}.get(x.get('priority', 'LOW'), 3))
        
        for i, task in enumerate(sorted_tasks[:7], 1):
            priority_marker = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '⚪'}.get(task.get('priority', 'LOW'), '⚪')
            agent = task.get('assigned_agent', 'UNASSIGNED')
            message_lines.append(f"{i}. {priority_marker} [{agent}] {task.get('task_name', 'Unknown')}")
        
        if len(sorted_tasks) > 7:
            message_lines.append(f"... и еще {len(sorted_tasks) - 7} задач")
        
        message_lines.append("")
        message_lines.append("<i>План сгенерирован автоматически AI Orchestrator</i>")
        
        message = '\n'.join(message_lines)
        
        notification = Notification(
            notification_id=f"MORNING-{today}",
            priority=NotificationPriority.MEDIUM.value,
            title=title,
            message=message,
            recipient='director',
            timestamp=datetime.now().isoformat(),
            metadata={
                'report_type': 'morning_plan',
                'total_tasks': len(tasks_planned)
            },
            requires_acknowledgment=False
        )
        
        return notification
    
    async def send_notification(self, notification: Notification) -> bool:
        """Отправка уведомления"""
        self.notifications_log.append(notification.to_dict())
        
        # Отправка в Telegram
        success = await self.send_telegram_message(notification.message)
        
        if success:
            self.logger.info(f"Уведомление {notification.notification_id} отправлено")
        else:
            self.logger.warning(f"Не удалось отправить уведомление {notification.notification_id}")
        
        # Логирование в файл
        self._log_to_file(notification)
        
        return success
    
    def _log_to_file(self, notification: Notification):
        """Логирование уведомления в файл"""
        log_entry = {
            'timestamp': notification.timestamp,
            'id': notification.notification_id,
            'priority': notification.priority,
            'title': notification.title,
            'recipient': notification.recipient
        }
        
        log_file = '/workspace/logs/notifications.log'
        try:
            import os
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Ошибка логирования: {e}")
    
    async def send_risk_alert(self, risk_card_data: Dict) -> bool:
        """Отправка предупреждения о риске"""
        notification = self.create_risk_notification(risk_card_data)
        return await self.send_notification(notification)
    
    async def send_daily_report(self, tasks_completed: List[Dict], tasks_planned: List[Dict]) -> bool:
        """Отправка ежедневного отчета"""
        notification = self.create_daily_report(tasks_completed, tasks_planned)
        return await self.send_notification(notification)
    
    async def send_morning_plan(self, tasks_planned: List[Dict]) -> bool:
        """Отправка утреннего плана"""
        notification = self.create_morning_plan(tasks_planned)
        return await self.send_notification(notification)


# Пример использования
if __name__ == "__main__":
    service = NotificationService()
    
    # Тестовая Risk Card
    test_risk_card = {
        'risk_id': 'RISK-20240115143022',
        'document_id': 'DOC-2024-001',
        'risk_score': 8,
        'risk_level': 'HIGH',
        'assessment_date': '2024-01-15T14:30:22',
        'critical_issues': [
            'КРИТИЧНО: Отсутствие допуска СРО',
            'КРИТИЧНО: Высокие финансовые риски'
        ],
        'recommendations': [
            'Немедленная эскалация директору',
            'Требуется внешняя юридическая экспертиза'
        ],
        'precedent_matches': [
            'PREC-2023-001: Нарушение сроков строительства',
            'PREC-2022-042: Невыполнение платежных обязательств'
        ]
    }
    
    # Тестовые задачи для отчета
    completed_tasks = [
        {'task_name': 'Оценка риска DOC-2024-001', 'success': True, 'details': 'Risk Score: 8/10'},
        {'task_name': 'Поиск прецедентов', 'success': True, 'details': 'Найдено 3 прецедента'},
        {'task_name': 'Генерация Risk Card', 'success': True, 'details': 'Экспорт в JSON выполнен'}
    ]
    
    planned_tasks = [
        {'task_name': 'Обработка входящих документов', 'priority': 'HIGH', 'assigned_agent': 'LEGAL_SHREDDER_AI'},
        {'task_name': 'Еженедельный аудит базы прецедентов', 'priority': 'MEDIUM', 'assigned_agent': 'COMPLIANCE_CHECKER'},
        {'task_name': 'Генерация еженедельного отчета', 'priority': 'LOW', 'assigned_agent': 'DOCUMENT_PROCESSING_AGENT'}
    ]
    
    print("Тест Notification Service запущен...")
    print("\nДля реальной отправки в Telegram необходимо настроить:")
    print("1. BOT_TOKEN в agents_config.yaml")
    print("2. CHAT_ID в agents_config.yaml")
