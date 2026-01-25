from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import AsyncSessionLocal
from models import User
from sqlalchemy import select
from keyboards.age_kb import get_age_kb
from keyboards.main_menu_kb import get_main_kb

router = Router()

@router.message(Command("start"))
async def command_start(message: Message):
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.age_group:
            await message.answer(
                "Привет! Для начала выбери свою возрастную группу:",
                reply_markup=get_age_kb()
            )
        else:
            await message.answer(
                "Добро пожаловать! Выберите раздел:",
                reply_markup=get_main_kb()  # Inline-меню вместо Reply
            )

@router.callback_query(F.data.startswith("age_"))
async def set_age_group(callback: CallbackQuery):
    age_map = {
        "age_young": "young",
        "age_teen": "teen",
        "age_student": "student"
    }
    
    age_group = age_map.get(callback.data)
    
    async with AsyncSessionLocal() as session:
        # ... та же логика сохранения в БД ...
        await session.commit()
    
    # Удаляем сообщение с выбором возраста
    await callback.message.delete()
    
    # Показываем главное меню
    await callback.message.answer(
        "✅ Возрастная группа сохранена!\n\n"
        "Теперь выберите раздел:",
        reply_markup=get_main_kb()
    )
    await callback.answer()