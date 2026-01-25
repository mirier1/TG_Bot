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

        if not user:
            # Новый пользователь
            await message.answer(
                "👋 Привет! Для начала выбери свою возрастную группу:",
                reply_markup=get_age_kb()
            )
        elif not user.age_group:
            # Пользователь есть, но возраст не выбран
            await message.answer(
                "📊 Выбери свою возрастную группу:",
                reply_markup=get_age_kb()
            )
        else:
            # Всё есть, показываем главное меню
            await message.answer(
                f"✅ Добро пожаловать, {user.username or 'пользователь'}!\n\n"
                "Выберите раздел:",
                reply_markup=get_main_kb()
            )

@router.callback_query(F.data.startswith("age_"))
async def set_age_inline(callback: CallbackQuery):
    age_map = {
        "age_young": "young",
        "age_teen": "teen", 
        "age_student": "student"
    }
    
    age_group = age_map.get(callback.data)
    
    if not age_group:
        await callback.answer("Ошибка выбора возраста")
        return
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == callback.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Создаём нового пользователя
            user = User(
                id=callback.from_user.id,
                username=callback.from_user.username or callback.from_user.first_name,
                age_group=age_group
            )
            session.add(user)
        else:
            # Обновляем существующего
            user.age_group = age_group
        
        await session.commit()
    
    # Удаляем сообщение с выбором возраста
    try:
        await callback.message.delete()
    except:
        pass
    
    # Показываем главное меню
    await callback.message.answer(
        f"✅ Возрастная группа сохранена!\n\n"
        "Теперь выберите раздел:",
        reply_markup=get_main_kb()
    )
    await callback.answer()