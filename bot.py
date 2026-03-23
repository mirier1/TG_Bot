import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
import aiohttp
from config import BOT_TOKEN
from database import create_table

from handlers.main_menu import router as main_menu_router
from handlers.sdg import router as sdg_router
from handlers.start import router as start_router
from handlers.settings import router as settings_router
from handlers.questions import router as questions_router
from handlers.admin import router as admin_router
from handlers.quizzes import router as quiz_router
from handlers.games import games_router
from handlers.ambassador import router as ambassador_router

# Настройка прокси для Tor
PROXY_URL = "socks5://127.0.0.1:9050"

async def main():
    # 1. Создаём таблицы в БД
    await create_table()
    print("✅ Таблицы созданы/проверены")
    
    # 2. Создаём сессию с прокси (правильный способ)
    connector = aiohttp.SocksConnector.from_url(PROXY_URL)
    session = aiohttp.ClientSession(connector=connector)
    
    # 3. Создаём бота с прокси
    aiogram_session = AiohttpSession(session=session)
    bot = Bot(token=BOT_TOKEN, session=aiogram_session)
    dp = Dispatcher()
    
    # 4. Подключаем все обработчики
    dp.include_router(sdg_router)
    dp.include_router(main_menu_router)
    dp.include_router(start_router)
    dp.include_router(settings_router)
    dp.include_router(questions_router)
    dp.include_router(admin_router)
    dp.include_router(quiz_router)
    dp.include_router(games_router)
    dp.include_router(ambassador_router)
    
    # 5. Запускаем бота
    print(f"🤖 Бот запущен через прокси: {PROXY_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())