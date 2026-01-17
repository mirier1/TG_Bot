import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.filters import Command
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

#Обработчик команды /start
@dp.message(Command("start"))
async def command_start(message: Message):
    await message.answer("Добро пожаловать! Выберите раздел:", reply_markup=get_main_kb())

@dp.message(F.text == "📚 Цели устойчивого развития")
async def handler_uroky(message: Message):
    await message.answer("Раздел в разработке")

@dp.message()
async def echo(message: Message):
    await message.answer("Привет! Бот работает.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())