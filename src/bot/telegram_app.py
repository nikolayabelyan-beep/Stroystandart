"""
Telegram Bot v2.2
Интеграция с Orchestrator для обработки документов и правок.
"""
import os
import sys
import logging
from telegram import Update, InputFile
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from io import BytesIO

# Добавляем путь к модулям
sys.path.insert(0, '/workspace/src/core')
from orchestrator import Orchestrator

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация оркестратора
orchestrator = Orchestrator()

# Токен и Chat ID из конфигурации
TELEGRAM_TOKEN = "8433856602:AAFY9Feuj0Z0UpJACktnCWJBWYHj3NISB8Y"
ADMIN_CHAT_ID = 245477113

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения и документы."""
    user_id = update.effective_user.id
    text = None
    
    # Игнорируем команду /start и другие команды
    if update.message.text and update.message.text.startswith('/'):
        return
    
    # Проверяем, есть ли документ
    if update.message.document:
        document = await update.message.document.get_file()
        file_bytes = await document.download_as_bytearray()
        file_content = bytes(file_bytes).decode('utf-8', errors='ignore')[:5000]
        
        if update.message.document.file_name.endswith(('.txt', '.md', '.json', '.csv')):
            text = file_content
        else:
            text = f"Документ: {update.message.document.file_name}\n{update.message.caption or ''}"
    elif update.message.text:
        text = update.message.text
    else:
        return
    
    if not text:
        return
    
    logger.info(f"Получено сообщение от пользователя {user_id}: {text[:100]}...")
    
    try:
        result = orchestrator.process_message(text, user_id)
        
        if result['status'] == 'error':
            await update.message.reply_text(result['message'])
            return
        
        analysis = result['analysis']
        
        # Формируем текстовый отчет
        response_text = f"""
📊 {result['message']}

🔍 ДЕТАЛЬНЫЙ АНАЛИЗ:

1️⃣ ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ ({len(analysis['detected_issues'])}):
{chr(10).join(['• ' + issue for issue in analysis['detected_issues']] or ['• Проблем не выявлено'])}

2️⃣ РЕКОМЕНДАЦИИ ЮРИСТА:
{chr(10).join(['✓ ' + rec for rec in analysis['recommendations']])}

3️⃣ ФИНАНСОВЫЕ РИСКИ: {"⚠️ Выявлены" if analysis['financial_exposure'] else "✅ Не выявлены"}

---
💡 Для создания файла .docx напишите: "создай файл", "сделай документ", "подготовь письмо"
💡 Ваша правка будет учтена, если напишете: "исправь...", "добавь...", "измени..."
        """.strip()
        
        await update.message.reply_text(response_text)
        
        # Генерируем файл .docx только по явному запросу
        if any(keyword in text.lower() for keyword in ['создай файл', 'сделай документ', 'подготовь письмо', 'сохрани как', 'экспортируй']):
            docx_content = orchestrator.generate_docx(analysis)
            doc_file = BytesIO(docx_content)
            doc_file.name = f"legal_report_{analysis['risk_level']}_{analysis['risk_score']}.docx"
            
            await update.message.reply_document(
                document=InputFile(doc_file),
                caption=f"📄 Полный юридический отчет (Риск: {analysis['risk_score']}/10)"
            )
            logger.info(f"Файл .docx отправлен пользователю {user_id}")
        else:
            logger.info(f"Текстовый отчет отправлен пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка обработки: {str(e)}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start."""
    await update.message.reply_text("""
🤖 ИИ-Юрист ООО "СТРОЙСТАНДАРТ" активирован!

📋 Что я умею:
• Анализировать договоры, жалобы, акты
• Оценивать юридические риски (1-10)
• Генерировать готовые документы (.docx)
• Учитывать ваши правки и создавать правила

📤 Отправьте мне документ или текст для анализа.
✏️ Для правки напишите: "исправь...", "добавь...", "измени..."

🕒 Утренний план: 08:00 | Вечерний отчет: 18:00
    """)

def main():
    """Запуск бота."""
    logger.info("Запуск Telegram бота v2.2...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчики
    application.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, handle_message))
    application.add_handler(CommandHandler('start', start_command))
    
    logger.info("Бот запущен и ожидает сообщения...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
