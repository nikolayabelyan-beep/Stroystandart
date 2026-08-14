import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("bot_debug.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

if not DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY не найден! Бот не сможет работать без ключа.")
    sys.exit(1) # Теперь бот не запустится без ключа

LOG_FILE = "orchestrator_log.json"

# --- ИНТЕГРАЦИЯ С DEEPSEEK (МОЗГ) ---
async def ask_deepseek(prompt: str, user_history: list = None) -> str:
    """Отправляет запрос к DeepSeek API и возвращает ответ."""
    import aiohttp
    
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    system_prompt = (
        "Ты — ИИ-ассистент Генерального директора строительной компании ООО 'СТРОЙСТАНДАРТ'. "
        "Твой стиль: деловой, лаконичный, конкретный, без воды. "
        "Ты отвечаешь на вопросы, анализируешь риски и составляешь документы. "
        "КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:\n"
        "1. ЗАПРЕЩЕНО отправлять шаблонные фразы типа 'Анализ завершен', 'Риск LOW/HIGH', 'ДЕТАЛЬНЫЙ АНАЛИЗ', 'ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ' без реального содержания.\n"
        "2. Каждый ответ должен быть уникальным и соответствовать конкретному запросу пользователя.\n"
        "3. Если пользователь просит создать документ (письмо, договор, жалобу), в КОНЦЕ ответа добавь строку: 'FILE_REQUEST: <название файла>.docx'.\n"
        "4. Если это вопрос, приветствие или обсуждение — НЕ создавай файлы и НЕ пиши шаблоны.\n"
        "5. Отвечай сразу по делу, без вступлений типа 'Конечно', 'Давайте разберем'.\n"
        "6. Никогда не пиши структуру отчёта с пунктами 1️⃣2️⃣3️⃣4️⃣ если пользователь явно не просил формат отчёта."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if user_history:
        messages.extend(user_history[-10:]) # Последние 10 сообщений для контекста
    messages.append({"role": "user", "content": prompt})

    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"Отправка запроса к DeepSeek API: {prompt[:50]}...") # Лог отправки
            async with session.post(url, json={"model": "deepseek-chat", "messages": messages}, headers=headers) as resp:
                logger.info(f"Получен ответ от DeepSeek со статусом: {resp.status}") # Лог ответа
                if resp.status == 200:
                    data = await resp.json()
                    response_text = data["choices"][0]["message"]["content"]
                    logger.info(f"Ответ DeepSeek: {response_text[:100]}...") # Лог содержимого
                    return response_text
                else:
                    error_text = await resp.text()
                    logger.error(f"DeepSeek API Error: {resp.status} - {error_text}")
                    return f"Ошибка связи с сервером аналитики (код {resp.status}). Попробуйте позже."
    except Exception as e:
        logger.error(f"Connection error to DeepSeek: {e}", exc_info=True) # Полный лог ошибки
        return "Техническая ошибка соединения."

# --- ЛОГИРОВАНИЕ ДЕЙСТВИЙ ОРКЕСТРАТОРА ---
def log_action(user_id: int, text: str, ai_response: str, file_created: str = None):
    """Записывает действие в лог-файл."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "input": text,
        "ai_response_preview": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
        "file_created": file_created,
        "status": "success"
    }
    
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
    
    logs.append(entry)
    # Храним последние 50 записей
    logs = logs[-50:]
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# --- ОБРАБОТЧИКИ КОМАНД И СООБЩЕНИЙ ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start. ТОЛЬКО ТЕКСТ."""
    user = update.effective_user
    welcome_text = (
        f"Здравствуйте, {user.first_name}!\n\n"
        "Я — ваш ИИ-помощник Генерального директора ООО 'СТРОЙСТАНДАРТ'.\n\n"
        "🏗 **Чем я могу помочь:**\n"
        "• Анализ договоров и рисков\n"
        "• Составление писем, претензий, жалоб (в ФАС, суд)\n"
        "• Поиск судебных прецедентов\n"
        "• Консультации по 44-ФЗ, 223-ФЗ, ГК РФ\n\n"
        "Просто напишите вашу задачу или отправьте документ."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    # Логируем старт
    log_action(user.id, "/start", "Welcome message sent", None)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений."""
    user = update.effective_user
    text = update.message.text
    
    if not text:
        return

    # Индикатор набора
    await update.message.chat.send_action(action='typing')

    # Получаем историю из контекста (упрощенно)
    history = context.user_data.get('history', [])
    
    # Запрос к ИИ
    ai_response = await ask_deepseek(text, history)
    
    # Обновляем историю
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": ai_response})
    context.user_data['history'] = history

    # Проверка на запрос файла
    file_to_send = None
    file_name = None
    
    if "FILE_REQUEST:" in ai_response:
        # Извлекаем имя файла
        parts = ai_response.split("FILE_REQUEST:")
        clean_text = parts[0].strip()
        file_name_raw = parts[1].strip().split('\n')[0].strip()
        file_name = file_name_raw.replace('"', '').replace("'", "")
        
        # Генерация документа через document_generator
        from src.core.document_generator import generate_document
        
        try:
            doc_path = generate_document(clean_text, file_name)
            file_to_send = doc_path
            ai_response = clean_text 
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            ai_response += "\n(Ошибка при создании файла)"

    # Отправка текста
    await update.message.reply_text(ai_response, parse_mode='Markdown')

    # Отправка файла (если есть)
    if file_to_send and os.path.exists(file_to_send):
        try:
            with open(file_to_send, 'rb') as f:
                await update.message.reply_document(document=f, filename=file_name)
            # Удаляем временный файл
            os.remove(file_to_send)
        except Exception as e:
            logger.error(f"Error sending file: {e}")

    # Логирование
    log_action(user.id, text, ai_response, file_name)

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
    
    # Скачиваем файл для анализа
    file = await context.bot.get_file(doc.file_id)
    file_path = f"temp_{file_name}"
    await file.download_to_drive(file_path)
    
    try:
        # Отправляем документ в DeepSeek для анализа
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Формируем запрос к AI с контекстом файла
        ai_prompt = f"Проанализируй этот документ: {file_name}\n\nСодержание:\n{file_content.decode('utf-8', errors='ignore')[:5000]}"
        
        await update.message.chat.send_action(action='typing')
        ai_response = await ask_deepseek(ai_prompt, [])
        
        report = (
            f"✅ **Файл загружен:** `{file_name}`\n\n"
            f"📊 **Анализ документа:**\n{ai_response}"
        )
        
        await update.message.reply_text(report, parse_mode="Markdown")

    finally:
        # Удаляем временный файл
        if os.path.exists(file_path):
            os.remove(file_path)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    logger.info("Starting Telegram Bot (CEO Assistant Mode)...")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
