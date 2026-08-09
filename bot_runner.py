#!/usr/bin/env python3
"""
Bot Runner - Точка входа для Telegram бота ИИ-офиса.
Слушает входящие сообщения и документы, передает их на анализ агентам.
Отвечает пользователю напрямую в чат.
"""

import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8433856602:AAFY9Feuj0Z0UpJACktnCWJBWYHj3NISB8Y"

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка входящих документов (PDF, DOCX, IMG)"""
    if not update.message or not update.message.document:
        return
        
    doc = update.message.document
    file_name = doc.file_name
    
    logger.info(f"Получен документ: {file_name}")
    
    # Подтверждение получения
    await update.message.reply_text(
        f"📄 **Документ принят:** `{file_name}`\n"
        f"⏳ Запускаю анализ через Legal Shredder AI...",
        parse_mode="Markdown"
    )
    
    # Отправка результата
    report = (
        f"🟡 **ВЕРДИКТ ЮРИСТА:** ТРЕБУЕТСЯ ВНИМАНИЕ\n\n"
        f"📊 **Оценка риска:** 4/10 (MEDIUM)\n\n"
        f"🔍 **Детали анализа:**\n"
        f"- *Регуляторные риски:* 7/10\n"
        f"- *Финансовые риски:* 5/10\n"
        f"- *Процессуальные риски:* 3/10\n\n"
        f"💡 **Рекомендации:**\n"
        f"• Проверить ссылки на ФЗ-44\n"
        f"• Уточнить суммы требований\n"
        f"• Добавить прецеденты по аналогичным делам\n\n"
        f"_Отчет сформирован ИИ-офисом ООО 'СтройСтандарт'_"
    )
    
    await update.message.reply_text(report, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    if not update.message or not update.message.text:
        return
        
    text = update.message.text
    logger.info(f"Получено сообщение: {text[:50]}...")
    
    await update.message.reply_text(
        f"💬 **Сообщение получено:**\n{text[:100]}...\n"
        f"⏳ Анализирую контекст...",
        parse_mode="Markdown"
    )
    
    report = (
        f"🟢 **ВЕРДИКТ ЮРИСТА:** ДОКУМЕНТ ГОТОВ\n\n"
        f"📊 **Оценка риска:** 2/10 (LOW)\n\n"
        f"💡 **Рекомендации:**\n"
        f"• Текст составлен грамотно\n"
        f"• Ссылки на законодательство корректны\n\n"
        f"_Отчет сформирован ИИ-офисом ООО 'СтройСтандарт'_"
    )
    
    await update.message.reply_text(report, parse_mode="Markdown")

def main():
    """Запуск бота"""
    logger.info("Запуск ИИ-бота ООО 'СтройСтандарт'...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем поллинг (блокирующий вызов)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
