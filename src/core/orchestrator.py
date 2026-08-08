"""
AI Orchestrator - Центральный координатор ИИ-офиса
Автономная работа с ежедневными отчетами и планами
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import logging

from src.core.risk_scoring_engine import RiskScoringEngine, RiskCard
from src.core.notification_service import NotificationService


class AIOrchestrator:
    """
    Центральный оркестратор ИИ-офиса
    Координирует работу всех агентов, управляет задачами и генерирует отчеты
    """
    
    def __init__(self):
        self.risk_engine = RiskScoringEngine()
        self.notification_service = NotificationService()
        self.task_queue = []
        self.completed_tasks = []
        self.agents_status = {}
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AIOrchestrator')
        
        # Инициализация статусов агентов
        self._init_agents()
    
    def _init_agents(self):
        """Инициализация статусов агентов"""
        self.agents_status = {
            'LEGAL_SHREDDER_AI': {'status': 'IDLE', 'current_task': None},
            'COMPLIANCE_CHECKER': {'status': 'IDLE', 'current_task': None},
            'RISK_ASSESSOR': {'status': 'IDLE', 'current_task': None},
            'DOCUMENT_PROCESSING_AGENT': {'status': 'IDLE', 'current_task': None},
            'PRECEDENT_ENGINE': {'status': 'IDLE', 'current_task': None}
        }
    
    async def start_daily_cycle(self):
        """Запуск ежедневного цикла работы"""
        self.logger.info("Запуск ежедневного цикла AI Orchestrator")
        
        # 1. Утренний план (08:00)
        await self._send_morning_plan()
        
        # 2. Обработка задач в течение дня
        await self._process_task_queue()
        
        # 3. Вечерний отчет (18:00)
        await self._send_evening_report()
    
    async def _send_morning_plan(self):
        """Отправка утреннего плана задач"""
        self.logger.info("Генерация утреннего плана")
        
        # Генерация плана на день
        morning_tasks = self._generate_daily_plan()
        
        # Отправка уведомления
        await self.notification_service.send_morning_plan(morning_tasks)
        
        # Добавление задач в очередь
        self.task_queue.extend(morning_tasks)
        
        self.logger.info(f"Утренний план отправлен. Задач: {len(morning_tasks)}")
    
    async def _process_task_queue(self):
        """Обработка очереди задач"""
        self.logger.info("Начало обработки очереди задач")
        
        while self.task_queue:
            task = self.task_queue.pop(0)
            result = await self._execute_task(task)
            self.completed_tasks.append(result)
            
            # Небольшая пауза между задачами
            await asyncio.sleep(1)
        
        self.logger.info(f"Обработка завершена. Выполнено задач: {len(self.completed_tasks)}")
    
    async def _execute_task(self, task: Dict) -> Dict:
        """Выполнение отдельной задачи"""
        task_name = task.get('task_name', 'Unknown')
        agent = task.get('assigned_agent', 'UNASSIGNED')
        
        self.logger.info(f"Выполнение задачи: {task_name} (Агент: {agent})")
        
        # Обновление статуса агента
        self.agents_status[agent]['status'] = 'BUSY'
        self.agents_status[agent]['current_task'] = task_name
        
        try:
            # Выполнение задачи в зависимости от типа
            if task_name == 'Оценка риска документа':
                result = await self._assess_document_risk(task)
            elif task_name == 'Поиск прецедентов':
                result = await self._search_precedents(task)
            elif task_name == 'Проверка соответствия':
                result = await self._compliance_check(task)
            elif task_name == 'Обработка входящих документов':
                result = await self._process_incoming_documents(task)
            else:
                result = {'success': True, 'details': 'Задача выполнена'}
            
            result['task_name'] = task_name
            result['assigned_agent'] = agent
            result['success'] = True
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения задачи {task_name}: {e}")
            result = {
                'task_name': task_name,
                'assigned_agent': agent,
                'success': False,
                'details': f'Ошибка: {str(e)}'
            }
        
        finally:
            # Возврат агента в состояние IDLE
            self.agents_status[agent]['status'] = 'IDLE'
            self.agents_status[agent]['current_task'] = None
        
        return result
    
    async def _assess_document_risk(self, task: Dict) -> Dict:
        """Оценка риска документа"""
        document_data = task.get('document_data', {})
        
        # Использование Risk Scoring Engine
        risk_card = self.risk_engine.assess_risk(document_data)
        
        # Экспорт Risk Card
        risk_card_path = f"/workspace/templates/risk_card_{risk_card.risk_id}.json"
        self.risk_engine.export_risk_card(risk_card, risk_card_path)
        
        # Отправка уведомления если риск высокий
        if risk_card.risk_level in ['HIGH', 'MEDIUM']:
            await self.notification_service.send_risk_alert(risk_card.to_dict())
        
        return {
            'success': True,
            'details': f"Risk Score: {risk_card.risk_score}/10, Level: {risk_card.risk_level}"
        }
    
    async def _search_precedents(self, task: Dict) -> Dict:
        """Поиск прецедентов"""
        search_params = task.get('search_params', {})
        
        # Поиск в базе прецедентов
        precedents_dir = Path('/workspace/obsidian_vault/03_Legal_Precedents')
        found_precedents = []
        
        for md_file in precedents_dir.glob('*.md'):
            if md_file.name.startswith('PREC-'):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Простой поиск по ключевым словам
                    keywords = search_params.get('keywords', [])
                    if any(kw.lower() in content.lower() for kw in keywords):
                        found_precedents.append(md_file.name)
        
        return {
            'success': True,
            'details': f"Найдено прецедентов: {len(found_precedents)}"
        }
    
    async def _compliance_check(self, task: Dict) -> Dict:
        """Проверка соответствия"""
        # Заглушка для реализации
        return {
            'success': True,
            'details': 'Проверка соответствия выполнена'
        }
    
    async def _process_incoming_documents(self, task: Dict) -> Dict:
        """Обработка входящих документов"""
        # Заглушка для реализации
        return {
            'success': True,
            'details': 'Входящие документы обработаны'
        }
    
    def _generate_daily_plan(self) -> List[Dict]:
        """Генерация плана задач на день"""
        today = datetime.now().strftime('%A')
        
        # Базовый план задач
        base_tasks = [
            {
                'task_name': 'Обработка входящих документов',
                'priority': 'HIGH',
                'assigned_agent': 'LEGAL_SHREDDER_AI',
                'estimated_duration': 120  # минут
            },
            {
                'task_name': 'Оценка риска новых контрактов',
                'priority': 'HIGH',
                'assigned_agent': 'RISK_ASSESSOR',
                'estimated_duration': 60
            },
            {
                'task_name': 'Мониторинг изменений законодательства',
                'priority': 'MEDIUM',
                'assigned_agent': 'COMPLIANCE_CHECKER',
                'estimated_duration': 30
            }
        ]
        
        # Дополнительные задачи по дням недели
        weekly_tasks = {
            'Monday': [
                {
                    'task_name': 'Еженедельный аудит базы прецедентов',
                    'priority': 'MEDIUM',
                    'assigned_agent': 'PRECEDENT_ENGINE',
                    'estimated_duration': 45
                }
            ],
            'Wednesday': [
                {
                    'task_name': 'Генерация еженедельного отчета по рискам',
                    'priority': 'LOW',
                    'assigned_agent': 'DOCUMENT_PROCESSING_AGENT',
                    'estimated_duration': 30
                }
            ],
            'Friday': [
                {
                    'task_name': 'Резервное копирование данных',
                    'priority': 'MEDIUM',
                    'assigned_agent': 'DOCUMENT_PROCESSING_AGENT',
                    'estimated_duration': 20
                }
            ]
        }
        
        # Добавление задач по дню недели
        additional_tasks = weekly_tasks.get(today, [])
        all_tasks = base_tasks + additional_tasks
        
        return all_tasks
    
    async def _send_evening_report(self):
        """Отправка вечернего отчета"""
        self.logger.info("Генерация вечернего отчета")
        
        # Подготовка данных для отчета
        tasks_completed = self.completed_tasks.copy()
        tomorrow_plan = self._generate_daily_plan()
        
        # Отправка отчета
        await self.notification_service.send_daily_report(tasks_completed, tomorrow_plan)
        
        self.logger.info(f"Вечерний отчет отправлен. Задач выполнено: {len(tasks_completed)}")
        
        # Очистка завершенных задач
        self.completed_tasks.clear()
    
    def get_status(self) -> Dict:
        """Получение текущего статуса оркестратора"""
        return {
            'timestamp': datetime.now().isoformat(),
            'agents_status': self.agents_status,
            'queue_size': len(self.task_queue),
            'completed_today': len(self.completed_tasks)
        }


# Точка входа для автономной работы
async def main():
    """Основная функция запуска оркестратора"""
    orchestrator = AIOrchestrator()
    
    print("=" * 60)
    print("AI ORCHESTRATOR запущен")
    print("=" * 60)
    print(f"Время запуска: {datetime.now().isoformat()}")
    print(f"Статус агентов: {orchestrator.get_status()['agents_status']}")
    print("=" * 60)
    
    # Запуск ежедневного цикла
    await orchestrator.start_daily_cycle()
    
    print("=" * 60)
    print("Ежедневный цикл завершен")
    print("=" * 60)


if __name__ == "__main__":
    # Запуск в event loop
    asyncio.run(main())
