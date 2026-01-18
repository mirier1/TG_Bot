import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.filters import Command
from config import BOT_TOKEN
from database import create_table
from database import AsyncSessionLocal
from models import User
from sqlalchemy import select

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

#КЛАВИАТУРА -----------------
#Создаем клавиатуру для главного меню
def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Цели устойчивого развития")],
            [KeyboardButton(text="🎮 Мини-игры")],
            [KeyboardButton(text="❓ Вопрос эксперту")],
            [KeyboardButton(text="🎓 Стать посланником ЦУР")],
            [KeyboardButton(text="🎥 Конкурс «Я есть ЦУР»")],
            [KeyboardButton(text="📊 Обратная связь")]
        ],
        resize_keyboard=True
    )

def get_age_kb():
    return ReplyKeyboardMarkup (
        keyboard=[
            [KeyboardButton(text="5-7 класс")],
            [KeyboardButton(text="9-11 класс")],
            [KeyboardButton(text="Студент")]
        ],
        resize_keyboard=True
    )

#----------------------------
#Обработчик команды /start
@dp.message(Command("start"))
async def command_start(message: Message):
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(
                "Привет! Для начала выбери свою возрастную группу:",
                reply_markup=get_age_kb()
            )
        elif not user.age_group:
            await message.answer(
                "Выбери свою возрастную группу:",
                reply_markup=get_age_kb()
            )
        else:
            await message.answer(
                "Добро пожаловать! Выберите раздел:",
                reply_markup=get_main_kb()
            )

@dp.message(F.text.in_(["5-7 класс", "9-11 класс", "Студент"]))
async def set_age_group(message: Message):
    age_map = {
        "5-7 класс": "young",
        "9-11 класс": "teen",
        "Студент": "student"
    }
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Создаём нового пользователя
            user = User(
                id=message.from_user.id,
                username=message.from_user.username or message.from_user.first_name or "Пользователь",
                age_group=age_map[message.text]
            )
            session.add(user)
        else:
            # Обновляем существующего
            user.age_group = age_map[message.text]
        
        await session.commit()
    
    await message.answer(
        "Отлично! Теперь ты можешь пользоваться ботом.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📚 Цели устойчивого развития")
async def handler_uroky(message: Message):
    await message.answer("Раздел в разработке")

@dp.message()
async def echo(message: Message):
    await message.answer("Привет! Бот работает.")

async def on_startup():
    await create_table()
    print("✅ Таблицы созданы/проверены")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())