import asyncio
from aiogram import Bot, Dispatcher
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
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(sdg_router)
dp.include_router(main_menu_router)
dp.include_router(start_router)
dp.include_router(settings_router)
dp.include_router(questions_router)
dp.include_router(admin_router)
dp.include_router(quiz_router)
dp.include_router(games_router)

async def on_startup():
    await create_table()
    print("✅ Таблицы созданы/проверены")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
