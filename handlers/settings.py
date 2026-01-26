from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import AsyncSessionLocal
from models import User
from sqlalchemy import select
from keyboards.age_kb import get_age_kb
from keyboards.main_menu_kb import get_main_kb
from keyboards.settings_kb import get_settings_kb

router = Router()

@router.callback_query(F.data == "menu_settings")
async def show_settings(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        "⚙️ **Настройки профиля**\n\n"
        "Здесь вы можете изменить свои данные:",
        reply_markup=get_settings_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "settings_change_age")
async def change_age(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        "Выберите новую возрастную группу:",
        reply_markup=get_age_kb()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("age_"))
async def process_new_age(callback: CallbackQuery):
    age_map = {
        "age_young": "young",
        "age_teen": "teen", 
        "age_student": "student"
    }
    
    age_group = age_map.get(callback.data)
    
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == callback.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            user.age_group = age_group
            await session.commit()
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        f"✅ Возрастная группа обновлена!\n\n"
        "Возвращаемся в главное меню:",
        reply_markup=get_main_kb()
    )
    await callback.answer()