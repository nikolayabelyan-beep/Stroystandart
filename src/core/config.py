import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv(override=True)


# Базовые директории проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OBSIDIAN_VAULT_DIR = Path(os.getenv("OBSIDIAN_VAULT_PATH", str(BASE_DIR / "obsidian_vault")))
OUTPUT_DIR = BASE_DIR / "output"
LEGAL_UPDATES_DIR = BASE_DIR / "data" / "legal_updates"
LEGAL_SOURCES_PATH = LEGAL_UPDATES_DIR / "sources.json"
LEGAL_STATE_PATH = LEGAL_UPDATES_DIR / "state.json"
LEGAL_REPORTS_DIR = BASE_DIR / "obsidian_vault" / "01_Law" / "Updates"

# Векторная база данных
QDRANT_DB_DIR = DATA_DIR / "qdrant_db"

# Определение провайдера по умолчанию
DEFAULT_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_BASE = os.getenv("GOOGLE_API_BASE")


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Email настройки
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)
CEO_EMAIL = os.getenv("CEO_EMAIL")  # Email генерального директора для отчетов


def ensure_directories():
    """Создает необходимые директории, если их нет"""
    for directory in [DATA_DIR, OBSIDIAN_VAULT_DIR, OUTPUT_DIR, QDRANT_DB_DIR, LEGAL_UPDATES_DIR, LEGAL_REPORTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

ensure_directories()
