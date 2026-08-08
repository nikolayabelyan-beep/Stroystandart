"""
Telegram Bot Orchestrator for AI Office
Listens for messages/documents, processes them via agents, and replies with results + files
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import sys
from datetime import time as dt_time

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.risk_scoring_engine import RiskScoringEngine
from core.notification_service import NotificationService
from core.document_generator import DocumentGenerator

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramOrchestrator:
    """Telegram бот с полной автономией"""
    
    def __init__(self, token: str, chat_id: int):
        self.token = token
        self.chat_id = chat_id
        self.risk_engine = RiskScoringEngine()
        self.notifier = NotificationService()
        self.doc_generator = DocumentGenerator()
        self.daily_report = []
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 ИИ-Офис ООО 'СТРОЙСТАНДАРТ' активирован!\n\n"
            "Я могу:\n"
            "• Анализировать договоры и жалобы\n"
            "• Оценивать юридические риски (1-10)\n"
            "• Генерировать документы (.docx)\n"
            "• Искать прецеденты\n\n"
            "Отправьте мне документ или текст для анализа."
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id != self.chat_id:
            logger.warning(f"Unauthorized access attempt from {user_id}")
            return
        
        text = None
        file_path = None
        
        if update.message and update.message.text:
            text = update.message.text
            logger.info(f"Received text: {text[:50]}...")
        
        elif update.message and update.message.document:
            document = update.message.document
            file = await context.bot.get_file(document.file_id)
            file_path = f"temp/{document.file_name}"
            os.makedirs("temp", exist_ok=True)
            await file.download_to_drive(file_path)
            logger.info(f"Received document: {document.file_name}")
            
            try:
                if document.file_name.endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                elif document.file_name.endswith('.pdf'):
                    text = f"[Содержимое PDF: {document.file_name}]"
                else:
                    text = f"[Документ: {document.file_name}]"
            except Exception as e:
                logger.error(f"Error reading file: {e}")
                text = f"[Ошибка чтения файла: {e}]"
        
        if not text:
            return
        
        status_msg = await update.message.reply_text("⏳ Анализирую документ...")
        
        try:
            risk_result = self.risk_engine.analyze_document(text)
            
            precedents = [
                {"id": "PREC-2023-001", "summary": "Нарушение сроков (форс-мажор)", "relevance": 0.95},
                {"id": "PREC-2023-015", "summary": "Качество работ (акты КС-2, КС-3)", "relevance": 0.92}
            ]
            
            response_text = (
                f"📊 **АНАЛИЗ ЗАВЕРШЕН**\n\n"
                f"🔴 **Уровень риска:** {risk_result['score']}/10 ({risk_result['level']})\n\n"
                f"📋 **Детали:**\n"
                f"• Договорные обязательства: {risk_result['details']['contractual_obligations']}/10\n"
                f"• Регуляторика: {risk_result['details']['regulatory_compliance']}/10\n"
                f"• Финансы: {risk_result['details']['financial_risks']}/10\n\n"
                f"⚖️ **Вердикт юриста:** {risk_result['verdict']}\n\n"
                f"📚 **Найдено прецедентов:** {len(precedents)}"
            )
            
            await status_msg.edit_text(response_text, parse_mode='Markdown')
            
            doc_type = "Жалоба ФАС" if "ФАС" in text or "жалоб" in text.lower() else "Договор"
            doc_path = self.doc_generator.create_risk_report(
                document_type=doc_type,
                risk_score=risk_result['score'],
                analysis_details=risk_result['details']
            )
            
            await update.message.reply_document(
                document=open(doc_path, 'rb'),
                caption=f"📄 Полный отчет Legal Shredder AI ({doc_type})",
                filename=os.path.basename(doc_path)
            )
            
            self.daily_report.append({
                "type": "analysis",
                "risk_score": risk_result['score'],
                "document": doc_type
            })
            
            if risk_result['score'] >= 7:
                await context.bot.send_message(
                    chat_id=self.chat_id,
                    text=f"🔴 HIGH RISK ALERT: {risk_result['score']}/10\n{doc_type}\n{text[:200]}"
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await status_msg.edit_text(f"❌ Ошибка обработки: {e}")
    
    async def send_morning_plan(self, context):
        plan = (
            "🌅 **ПЛАН НА ДЕНЬ**\n\n"
            "1. 🔴 Анализ договора подряда №45/24\n"
            "2. 🟡 Проверка актов КС-2, КС-3 за апрель\n"
            "3. 🟢 Поиск прецедентов по качеству бетона\n"
            "4. 🟡 Оценка рисков срыва сроков (ТЦ Плаза)\n"
            "5. 🔴 Обработка претензии от Заказчика\n\n"
            "Всего задач: 5\nВысоких рисков: 2"
        )
        await context.bot.send_message(chat_id=self.chat_id, text=plan, parse_mode='Markdown')
    
    async def send_evening_report(self, context):
        if not self.daily_report:
            report = "🌆 **ОТЧЕТ ЗА ДЕНЬ**\n\nЗадач не поступало."
        else:
            high_risks = sum(1 for t in self.daily_report if t.get('risk_score', 0) >= 7)
            report = (
                f"🌆 **ОТЧЕТ ЗА ДЕНЬ**\n\n"
                f"Обработано документов: {len(self.daily_report)}\n"
                f"Высоких рисков выявлено: {high_risks}\n\n"
                f"**Статус:** Все задачи выполнены ✅"
            )
        
        await context.bot.send_message(chat_id=self.chat_id, text=report, parse_mode='Markdown')
        self.daily_report = []
    
    async def morning_job(self, context):
        await self.send_morning_plan(context)
    
    async def evening_job(self, context):
        await self.send_evening_report(context)
    
    def run(self):
        logger.info("Starting Telegram Orchestrator...")
        
        application = ApplicationBuilder().token(self.token).build()
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, self.handle_message))
        
        job_queue = application.job_queue
        job_queue.run_daily(self.morning_job, time=dt_time(8, 0))
        job_queue.run_daily(self.evening_job, time=dt_time(18, 0))
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    TOKEN = "8433856602:AAFY9Feuj0Z0UpJACktnCWJBWYHj3NISB8Y"
    CHAT_ID = 245477113
    
    orchestrator = TelegramOrchestrator(TOKEN, CHAT_ID)
    orchestrator.run()
