import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Токен сообщества VK (Настройки → Работа с API → Ключи доступа)
VK_TOKEN = os.getenv("VK_TOKEN", "")

# ID сообщества без минуса, например 123456789
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))

# PostgreSQL для заявок (общая БД с backend)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://shini:shini@localhost:5432/shini",
)

# SQLite для каталога шин в боте
TIRES_DATABASE_URL = os.getenv("TIRES_DATABASE_URL", f"sqlite:///{BASE_DIR / 'tires.db'}")

# Ссылка на сайт / группу
SITE_URL = os.getenv("SITE_URL", "https://shini-phi.vercel.app")
VK_GROUP_URL = os.getenv("VK_GROUP_URL", "https://vk.com/kolesadeshevo")

# Сколько позиций показывать в ответе
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "10"))
