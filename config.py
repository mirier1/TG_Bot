import os
from dotenv import load_dotenv

# Загружаем .env только для локальной разработки
load_dotenv()

def get_env_var(name: str, required: bool = True) -> str:
    """Получает переменную окружения, если required=True и её нет — выбрасывает ошибку"""
    value = os.getenv(name)
    if required and value is None:
        raise ValueError(f"❌ Переменная окружения {name} не задана!")
    return value

# Токен бота
BOT_TOKEN = get_env_var("BOT_TOKEN")

# ID администратора (может быть отрицательным для чата)
ADMIN_CHAT_ID_RAW = get_env_var("ADMIN_CHAT_ID")
try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_RAW)
except ValueError:
    raise ValueError(f"❌ ADMIN_CHAT_ID должен быть числом, получено: {ADMIN_CHAT_ID_RAW}")

# Список ID администраторов
ADMIN_IDS_RAW = get_env_var("ADMIN_IDS")
ADMIN_IDS = []
if ADMIN_IDS_RAW:
    for id_str in ADMIN_IDS_RAW.split(","):
        id_str = id_str.strip()
        if id_str:
            try:
                ADMIN_IDS.append(int(id_str))
            except ValueError:
                print(f"⚠️ Предупреждение: {id_str} не является корректным ID")

print(f"✅ Конфигурация загружена. ADMIN_CHAT_ID={ADMIN_CHAT_ID}, ADMIN_IDS={ADMIN_IDS}")