import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import create_table

from handlers.main_menu import router as main_menu_router
from handlers.sdg import router as sdg_router
from handlers.start import router as start_router
from handlers.settings import router as settings_roiter
from handlers.questions import router as qustions_router
from handlers.admin import router as admin_router
from handlers.quizzes import router as quiz_router
from handlers.games import games_router
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
#Коментарий для теста
dp.include_router(sdg_router)
dp.include_router(main_menu_router)
dp.include_router(start_router)
dp.include_router(settings_roiter)
dp.include_router(qustions_router)
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