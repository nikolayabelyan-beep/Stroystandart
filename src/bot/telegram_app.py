import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_debug.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.core.config import TELEGRAM_BOT_TOKEN, OUTPUT_DIR
from src.tools.legal_updates_fetcher import run as run_legal_updates
from src.bot.history import add_message, get_history, clear_history
from src.crew.construction_firm import run_crew
from src.core.reporter import BusinessReporter

reporter = BusinessReporter()

# Сохраняем выбранного агента для каждого пользователя
user_agents = {}

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Группировка: Центр управления, Продакшн, Поддержка
    inline_keyboard = [
        [InlineKeyboardButton("🏆 ЦЕНТР УПРАВЛЕНИЯ", callback_data="header1")],
        [InlineKeyboardButton("👔 Директор (Эмин Ковальский)", callback_data="Исполнительный Директор")],
        [InlineKeyboardButton("🏗️ ПРОИЗВОДСТВЕННЫЙ БЛОК", callback_data="header2")],
        [InlineKeyboardButton("🔧 ПТО", callback_data="Инженер ПТО"), InlineKeyboardButton("⚖️ Юристы", callback_data="Юрист")],
        [InlineKeyboardButton("💰 ФИНАНСЫ И РОСТ", callback_data="header3")],
        [InlineKeyboardButton("💎 Фин. Директор", callback_data="Финансовый директор"), InlineKeyboardButton("🤝 Тендеры", callback_data="Продажи")],
        [InlineKeyboardButton("📂 СЕРВИСНЫЕ СЛУЖБЫ", callback_data="header4")],
        [InlineKeyboardButton("📦 Снабжение", callback_data="Снабженец"), InlineKeyboardButton("📅 Секретарь", callback_data="Секретарь")]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    reply_keyboard = [
        ["📈 ТЕКУЩАЯ ПРИБЫЛЬ", "📋 СТАТУС ЗАДАЧ"],
        ["🏢 МЕНЮ ОТДЕЛОВ", "📊 DASHBOARD"],
        ["🧹 ЧИСТКА ЛОГОВ", "❓ ПОДДЕРЖКА"]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    msg_text = (
        "👑 *ГЛАВНЫЙ КОМАНДНЫЙ ЦЕНТР*\n"
        "🏛 _ООО «СТРОЙСТАНДАРТ»_\n\n"
        "Выберите департамент для постановки задачи или анализа отчетности:"
    )
    
    if update.message:
        await update.message.reply_text(msg_text, reply_markup=inline_markup, parse_mode="Markdown")
        await update.message.reply_text("💼 Система автономного управления активирована.", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(msg_text, reply_markup=inline_markup, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_agents[chat_id] = "Исполнительный Директор"
    
    # Автоматический захват CHAT_ID для полной автоматизации
    try:
        with open(".env", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("TELEGRAM_CHAT_ID=") and (len(line.strip()) <= 17):
                new_lines.append(f"TELEGRAM_CHAT_ID={chat_id}\n")
                updated = True
                logger.info(f"CAPTURED CHAT_ID: {chat_id}")
            else:
                new_lines.append(line)
        
        if updated:
            with open(".env", "w", encoding="utf-8") as f:
                f.writelines(new_lines)
    except Exception as e:
        logger.error(f"Error saving chat_id: {e}")

    welcome_text = (
        "🏗 *Legal Construction Assistant: Management 2.0*\n\n"
        "Система переведена в режим **автономного управления**.\n"
        "Ваш основной контакт — **Исполнительный Директор**.\n\n"
        "Доступны новые функции:\n"
        "• 📈 Поиск и анализ тендеров (Продажи)\n"
        "• 💰 Контроль кассовых разрывов (Фин. Директор)\n"
        "• 🤝 Управление субподрядчиками и ВОР (Юрист)\n\n"
        "Используйте меню для переключения между отделами."
    )
    await show_main_menu(update, context)
    await update.effective_message.reply_text(welcome_text, parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_agent = query.data
    user_agents[update.effective_chat.id] = selected_agent
    
    role_info = ""
    if selected_agent == "Исполнительный Директор":
        role_info = "\n_Управляю всеми процессами, решаю задачи любой сложности._"
    elif selected_agent == "Финансовый директор":
        role_info = "\n_Контролирую Cash Flow и финансовые риски._"
    elif selected_agent == "Продажи":
        role_info = "\n_Анализирую тендеры и веду воронку лидов._"
    
    await query.edit_message_text(
        text=f"✅ *На связи: {selected_agent}*{role_info}\n\nОжидаю задачу или вводные данные.",
        parse_mode="Markdown"
    )

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"DEBUG: RECEIVED ANY UPDATE: {update}")
    if update.message:
        logger.info(f"DEBUG: MESSAGE TEXT: {update.message.text}")
        await handle_message(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text
    logger.info(f"DEBUG: Starting handle_message for {chat_id}")
    
    # Обработка кнопок статического меню (PREMIUM VERSION)
    cmd = user_text.upper()
    if "МЕНЮ ОТДЕЛОВ" in cmd:
        await show_main_menu(update, context)
        return
    elif "DASHBOARD" in cmd:
        await dashboard_cmd(update, context)
        return
    elif "ЧИСТКА ЛОГОВ" in cmd:
        clear_history(chat_id)
        await update.message.reply_text("🔴 *СИСТЕМА:* История диалога и кэш очищены.", parse_mode="Markdown")
        return
    elif "ПОДДЕРЖКА" in cmd:
        await help_cmd(update, context)
        return
    elif "ТЕКУЩАЯ ПРИБЫЛЬ" in cmd or "СТАТУС ЗАДАЧ" in cmd:
        await report_now_cmd(update, context)
        return

    agent = user_agents.get(chat_id, "Директор (Авто-распределение)")
    
    # Имитация раздумий
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    status_msg = await update.message.reply_text(f"⏳ *{agent}* готовит ответ...", parse_mode="Markdown")
    
    try:
        add_message(chat_id, "user", user_text)
        history = get_history(chat_id)
        existing_files = set(os.listdir(OUTPUT_DIR)) if os.path.exists(OUTPUT_DIR) else set()
        
        # Периодически обновляем "typing", если процесс долгий
        response = await asyncio.to_thread(run_crew, user_text, agent, history)
        
        add_message(chat_id, "assistant", response)
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
            
        new_files = set(os.listdir(OUTPUT_DIR)) - existing_files if os.path.exists(OUTPUT_DIR) else set()
        for nf in new_files:
            file_path = os.path.join(OUTPUT_DIR, nf)
            with open(file_path, 'rb') as doc:
                await context.bot.send_document(chat_id=chat_id, document=doc, caption=nf)
                
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Системная ошибка: {str(e)}")
    finally:
        try: await status_msg.delete()
        except: pass

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 /start - начало\n/menu - выбор отдела\n/dashboard - панель управления\n/clear - очистка\n/law_update - обновить юридическую базу",
        parse_mode="Markdown",
    )


async def law_update_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚖️ Запускаю обновление юридических источников...")
    try:
        report_path, new_count, error_count = await asyncio.to_thread(run_legal_updates, 25)
        text = (
            "✅ Обновление завершено.\n"
            f"Новых публикаций: {new_count}\n"
            f"Ошибок источников: {error_count}\n"
            f"Отчет: {report_path}"
        )
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка обновления юридической базы: {e}")

async def dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет кнопку с актуальной ссылкой на мобильный дашборд."""
    tunnel_file = Path("data/tunnel_url.txt")
    
    if tunnel_file.exists():
        url = tunnel_file.read_text(encoding="utf-8").strip()
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Открыть панель управления", url=url)]])
        await update.message.reply_text(
            f"🌐 *Командный Центр онлайн!*\n\nНажмите кнопку для открытия на iPhone:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⚠️ Туннель еще не запущен.\n\nЗапустите `python START_ALL.py` на вашем ПК, "
            "после чего ссылка придет автоматически.",
            parse_mode="Markdown"
        )

async def post_init(application):
    from telegram import BotCommand
    commands = [
        BotCommand("start", "Запуск"),
        BotCommand("menu", "Отделы"),
        BotCommand("dashboard", "Панель управления"),
        BotCommand("law_update", "Обновить правовую базу"),
        BotCommand("clear", "Очистка"),
        BotCommand("help", "Помощь")
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set")

async def get_working_request():
    """Проверяет прямой доступ и список популярных портов прокси (ВПН)."""
    import socket
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return None
    test_url = f"https://api.telegram.org/bot{token}/getMe"
    
    # Список портов для проверки (приоритет: Прямой -> .env -> Common)
    env_proxy = os.environ.get("HTTPS_PROXY")
    candidate_proxies = [None] # Сначала пробуем БЕЗ прокси (Direct)
    
    if env_proxy:
        candidate_proxies.append(env_proxy)
        
    # Популярные порты для Sing-box, Clash, V2Ray, Amnezia, Shadowsocks
    common_ports = [1111, 7890, 10808, 1080, 10809, 8888, 8889, 443, 80]
    
    # Расширяем список: для каждого порта пробуем и http, и socks5
    for p in common_ports:
        for proto in ["http", "socks5", "socks5h"]:
            p_url = f"{proto}://127.0.0.1:{p}"
            if p_url not in candidate_proxies:
                candidate_proxies.append(p_url)

    import httpx
    logger.info(f"Начинаю поиск рабочего пути к Telegram (всего вариантов: {len(candidate_proxies)})...")
    
    for proxy in candidate_proxies:
        try:
            proxy_type = "Direct" if proxy is None else f"{proxy}"
            
            # Используем AsyncClient для быстрой проверки с коротким таймаутом
            async with httpx.AsyncClient(proxy=proxy, timeout=3.0, verify=False, trust_env=False) as client:
                resp = await client.get(test_url)
                if resp.status_code == 200:
                    logger.info(f"СВЯЗЬ УСТАНОВЛЕНА: {proxy_type}")
                    return HTTPXRequest(
                        connect_timeout=30.0,
                        read_timeout=30.0,
                        proxy=proxy,
                        httpx_kwargs={"trust_env": False},
                    )
        except Exception:
            continue
            
    logger.warning("НЕ УДАЛОСЬ найти путь к Telegram. Бот будет пробовать снова через 10 сек...")
    return None

async def run_bot_instance():
    """Запуск одного экземпляра бота с текущими настройками сети."""
    load_dotenv(override=True)
    request = await get_working_request()
    
    if not request:
        return False # Не удалось найти сеть

    application = ApplicationBuilder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).request(request).post_init(post_init).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('menu', show_main_menu))
    application.add_handler(CommandHandler('clear', lambda u, c: clear_history(u.effective_chat.id)))
    application.add_handler(CommandHandler('help', help_cmd))
    application.add_handler(CommandHandler('dashboard', dashboard_cmd))
    application.add_handler(CommandHandler('law_update', law_update_cmd))
    application.add_handler(CommandHandler('report_now', report_now_cmd))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT, handle_any_message))

    logger.info("Starting polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Ждем вечно, пока работает поллинг
    # Запускаем планировщик отчетов
    asyncio.create_task(reporting_scheduler_task(application.bot))

    while application.updater.running:
        await asyncio.sleep(5)
    
    return True

async def report_now_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ручной вызов отчета для проверки."""
    await update.message.reply_text("Генерирую текущую сводку...")
    report = reporter.generate_morning_report(is_monday=False)
    await update.message.reply_text(report, parse_mode="Markdown")
    report_ev = reporter.generate_evening_report()
    await update.message.reply_text(report_ev, parse_mode="Markdown")

async def reporting_scheduler_task(bot):
    """Фоновая задача для отправки отчетов по расписанию."""
    logger.info("Планировщик отчетов запущен (08:00 и 20:00)")
    sent_morning = False
    sent_evening = False
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Сброс флагов в полночь
        if current_time == "00:00":
            sent_morning = False
            sent_evening = False

        # Утренний отчет (08:00)
        if current_time == "08:00" and not sent_morning:
            is_monday = (now.weekday() == 0)
            report = reporter.generate_morning_report(is_monday=is_monday)
            await broadcast_report(bot, report)
            sent_morning = True

        # Вечерний отчет (20:00)
        if current_time == "20:00" and not sent_evening:
            report = reporter.generate_evening_report()
            await broadcast_report(bot, report)
            sent_evening = True

        await asyncio.sleep(30) # Проверка каждые 30 секунд

async def broadcast_report(bot, text):
    """Отправляет отчет всем активным пользователям (или владельцу)."""
    # В этой версии шлем всем, кто хоть раз писал боту (из user_agents)
    for chat_id in user_agents.keys():
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ошибка отправки отчета пользователю {chat_id}: {e}")

async def main_async():
    """Главный цикл с авто-перезагрузкой при сетевых сбоях."""
    while True:
        try:
            success = await run_bot_instance()
            if not success:
                await asyncio.sleep(10)
                continue
        except Exception as e:
            logger.error(f"Критическая ошибка цикла бота: {e}")
            await asyncio.sleep(10)

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

if __name__ == '__main__':
    main()
