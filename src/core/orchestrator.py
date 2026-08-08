import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .risk_scoring_engine import RiskScoringEngine
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_engine = RiskScoringEngine()
        self.notification_service = NotificationService(config_path='agents_config.yaml')
        # Память активной сессии для обработки правок
        self.active_session = {
            "is_active": False,
            "document_id": None,
            "last_verdict": None,
            "original_content": "",
            "user_feedback_history": []
        }
        logger.info("Orchestrator initialized with session management")

    async def process_message(self, message_text: str, file_path: Optional[str] = None) -> str:
        """
        Обрабатывает входящее сообщение.
        Если есть активная сессия и статус ожидает правки -> обрабатывает как комментарий.
        Иначе -> начинает новый процесс анализа.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 1. Проверка: Это правка к предыдущему документу?
        if self.active_session["is_active"] and self.active_session.get("status") == "AWAITING_USER_FEEDBACK":
            logger.info(f"Получена правка пользователя для документа {self.active_session['document_id']}")
            return await self._handle_user_feedback(message_text)

        # 2. Новый запрос
        logger.info(f"Получен новый документ/запрос: {message_text[:50]}...")
        
        content = message_text
        if file_path:
            content = f"[Файл: {file_path}]\n{message_text}"
            # Здесь должна быть логика чтения файла (PDF/DOCX), пока эмулируем текстом
        
        # Запуск глубокого анализа
        analysis_result = await self._run_deep_analysis(content)
        
        # Сохранение сессии для будущих правок
        self.active_session.update({
            "is_active": True,
            "document_id": f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "AWAITING_USER_FEEDBACK",
            "last_verdict": analysis_result['verdict'],
            "original_content": content,
            "user_feedback_history": []
        })
        
        return analysis_result['report_text']

    async def _handle_user_feedback(self, feedback_text: str) -> str:
        """Обрабатывает комментарии пользователя и обновляет документ"""
        doc_id = self.active_session["document_id"]
        logger.info(f"Обработка правки для {doc_id}: {feedback_text}")
        
        # Сохраняем историю правок
        self.active_session["user_feedback_history"].append({
            "timestamp": datetime.now().isoformat(),
            "comment": feedback_text
        })
        
        # Передаем юристу на доработку с учетом комментариев
        updated_result = await self.risk_engine.revise_document(
            original_content=self.active_session["original_content"],
            previous_verdict=self.active_session["last_verdict"],
            user_comments=feedback_text,
            history=self.active_session["user_feedback_history"]
        )
        
        # Обновляем сессию
        self.active_session["last_verdict"] = updated_result['verdict']
        # Генерируем новый файл .docx с учетом правок
        file_path = await self._generate_docx(updated_result, suffix="_v2")
        
        response = (
            f"✅ **Правки приняты!**\\n\\n"
            f"Юрист обновил документ с учетом вашего комментария:\\n"
            f"_\"{feedback_text}\"_\\n\\n"
            f"📄 **Обновленный вердикт:** {updated_result['verdict']}\\n"
            f"📎 Файл с новой версией документа отправлен выше."
        )
        
        await self.notification_service.send_file(file_path, caption="Обновленная версия документа (v2)")
        return response

    async def _run_deep_analysis(self, content: str) -> Dict[str, Any]:
        """Запускает полный цикл анализа с детализацией"""
        # 1. Оценка рисков и детальный отчет
        risk_data = await self.risk_engine.analyze_full(content)
        
        # 2. Поиск прецедентов
        precedents = await self.risk_engine.find_precedents(content)
        
        # 3. Генерация итогового текста отчета
        report_text = self._format_detailed_report(risk_data, precedents)
        
        # 4. Генерация файла .docx
        file_path = await self._generate_docx(risk_data)
        
        # Отправка файла отдельно
        await self.notification_service.send_file(file_path, caption="📄 Полный юридический анализ и проект документа")
        
        return {"report_text": report_text, "verdict": risk_data['verdict']}

    def _format_detailed_report(self, risk_data: Dict, precedents: list) -> str:
        """Формирует детальный текстовый отчет для чата"""
        score = risk_data['score']
        level = risk_data['level']
        color = "🔴" if level == "HIGH" else "🟡" if level == "MEDIUM" else "🟢"
        
        report = (
            f"{color} **ДЕТАЛЬНЫЙ ЮРИДИЧЕСКИЙ АНАЛИЗ**\\n"
            f"🆔 Документ: {self.active_session['document_id']}\\n"
            f"⚖️ **Вердикт:** {risk_data['verdict']}\\n"
            f"📊 **Уровень риска:** {score}/10 ({level})\\n\\n"
            f"🔍 **Выявленные проблемы:**\\n"
            f"{risk_data['detailed_findings']}\\n\\n"
            f"⚖️ **Применимые нормы права:**\\n"
            f"{risk_data['legal_references']}\\n\\n"
            f"💡 **Рекомендации юриста:**\\n"
            f"{risk_data['recommendations']}\\n\\n"
            f"🏛 **Найденные прецеденты:**\\n"
            f"{self._format_precedents_list(precedents)}\\n\\n"
            f"📝 **Статус:** Ожидает ваших правок или подтверждения."
        )
        return report

    def _format_precedents_list(self, precedents: list) -> str:
        if not precedents:
            return "По релевантным прецедентам данных не найдено."
        res = ""
        for p in precedents[:3]:
            res += f"- {p['id']}: {p['summary']} (Релевантность: {p['relevance']})\\n"
        return res

    async def _generate_docx(self, data: Dict, suffix: str = "") -> str:
        """Генерирует .docx файл с полным отчетом и проектом письма"""
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document()
        
        # Заголовок
        heading = doc.add_heading('ЮРИДИЧЕСКОЕ ЗАКЛЮЧЕНИЕ И ПРОЕКТ ДОКУМЕНТА', 0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph(f"Дата анализа: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        doc.add_paragraph(f"ID документа: {self.active_session['document_id']}{suffix}")
        doc.add_paragraph("-" * 50)
        
        # Раздел 1: Анализ рисков
        doc.add_heading('1. АНАЛИЗ РИСКОВ', level=1)
        p_risk = doc.add_paragraph()
        p_risk.add_run('Оценка риска: ').bold = True
        p_risk.add_run(f"{data['score']}/10 ({data['level']})")
        
        doc.add_paragraph('Детальное описание проблем:', style='Intense Quote')
        doc.add_paragraph(data['detailed_findings'])
        
        # Раздел 2: Нормативная база
        doc.add_heading('2. НОРМАТИВНАЯ БАЗА', level=1)
        doc.add_paragraph(data['legal_references'])
        
        # Раздел 3: Рекомендации
        doc.add_heading('3. РЕКОМЕНДАЦИИ ЮРИСТА', level=1)
        doc.add_paragraph(data['recommendations'])
        
        # Раздел 4: Проект документа (Ответ/Жалоба/Письмо)
        doc.add_heading('4. ПРОЕКТ ДОКУМЕНТА (ГОТОВЫЙ ТЕКСТ)', level=1)
        doc.add_paragraph(data['draft_text'], style='No Spacing')
        
        filename = f"Legal_Report_{self.active_session['document_id']}{suffix}.docx"
        filepath = f"/tmp/{filename}"
        doc.save(filepath)
        return filepath

    async def send_morning_plan(self):
        plan = "☀️ **ПЛАН НА СЕГОДНЯ**\\n\\n1. Мониторинг входящих документов.\\n2. Анализ текущих рисков по активным контрактам.\\n3. Проверка сроков подачи отчетности.\\n\\n*Ожидаю ваши документы для работы.*"
        await self.notification_service.send_message(plan)

    async def send_evening_report(self):
        report = "🌆 **ОТЧЕТ ЗА ДЕНЬ**\\n\\n"
        if self.active_session["is_active"]:
            report += f"✅ Обработан документ: {self.active_session['document_id']}\\n"
            report += f"Статус: {self.active_session['status']}\\n"
            if self.active_session["user_feedback_history"]:
                report += f"Внесено правок пользователем: {len(self.active_session['user_feedback_history'])}\\n"
        else:
            report += "✅ Активных задач не было. Система в режиме ожидания.\\n"
        
        report += "\\n📅 **ПЛАН НА ЗАВТРА:**\\n- Продолжение мониторинга.\\n- Актуализация базы прецедентов."
        await self.notification_service.send_message(report)
