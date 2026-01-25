import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN
from database import create_table, AsyncSessionLocal
from models import User
from sqlalchemy import select

from utils.constants import SDG_TITLES
from handlers.main_menu import router as main_menu_router
from handlers.sdg import router as sdg_router
from handlers.start import router as start_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(sdg_router)
dp.include_router(main_menu_router)
dp.include_router(start_router)

async def on_startup():
    await create_table()
    print("✅ Таблицы созданы/проверены")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())