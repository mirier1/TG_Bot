from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

from database import AsyncSessionLocal
from models import SDGContent
from config import ADMIN_IDS
from utils.constants import SHORT_SDG_TITLES
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

router = Router()

class ContentForm(StatesGroup):
    waiting_text = State()
    waiting_video = State()

def is_admin_cb(callback: CallbackQuery) -> bool:
    return callback.from_user.id in ADMIN_IDS

# 1. Начало управления контентом
@router.callback_query(F.data == "admin_manage_sdg", F.func(is_admin_cb))
async def start_manage_sdg(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for i in range(1, 18):
        builder.button(text=SHORT_SDG_TITLES[i], callback_data=f"edit_sdg_{i}")
    builder.adjust(2)
    builder.row(InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="admin_back").buttons[0])
    
    await callback.message.edit_text("Выберите ЦУР для редактирования:", reply_markup=builder.as_markup())
    await callback.answer()

# 2. Выбор возраста для выбранной ЦУР
@router.callback_query(F.data.startswith("edit_sdg_"), F.func(is_admin_cb))
async def choose_age(callback: CallbackQuery):
    sdg_id = int(callback.data.split("_")[2])
    builder = InlineKeyboardBuilder()
    builder.button(text="1-4 класс", callback_data=f"edit_age_{sdg_id}_1-4")
    builder.button(text="5-8 класс", callback_data=f"edit_age_{sdg_id}_5-8")
    builder.button(text="9-11 класс", callback_data=f"edit_age_{sdg_id}_9-11")
    builder.button(text="Для всех", callback_data=f"edit_age_{sdg_id}_all")
    builder.adjust(1)
    
    await callback.message.edit_text(f"Выберите возрастную группу для ЦУР {sdg_id}:", reply_markup=builder.as_markup())
    await callback.answer()

# 3. Ожидание текста
@router.callback_query(F.data.startswith("edit_age_"), F.func(is_admin_cb))
async def wait_for_text(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    sdg_id = int(parts[2])
    age = parts[3]
    
    await state.update_data(sdg_id=sdg_id, age_group=age)
    await state.set_state(ContentForm.waiting_text)
    
    await callback.message.edit_text(
        f"Введите текст описания для ЦУР {sdg_id} (возраст: {age}).\n"
        "Если хотите оставить текущий текст без изменений, отправьте `/skip`."
    )
    await callback.answer()

# 4. Сохранение текста и запрос видео
@router.message(ContentForm.waiting_text)
async def save_text(message: Message, state: FSMContext):
    data = await state.get_data()
    text = message.text if message.text != "/skip" else None
    await state.update_data(description=text)
    await state.set_state(ContentForm.waiting_video)
    
    await message.answer("Отлично! Теперь отправьте ссылку на видео (YouTube/Rutube) или напишите `/skip`.")

# 5. Сохранение видео и запись в БД
@router.message(ContentForm.waiting_video)
async def save_video(message: Message, state: FSMContext):
    data = await state.get_data()
    video_url = message.text if message.text != "/skip" else None
    
    async with AsyncSessionLocal() as session:
        # Используем UPSERT (вставить или обновить)
        stmt = insert(SDGContent).values(
            sdg_id=data['sdg_id'],
            age_group=data['age_group'],
            description=data['description'] or "Текст будет добавлен позже.",
            video_url=video_url
        )
        stmt = stmt.on_conflict_do_update(
            constraint='uq_sdg_age',
            set_=dict(
                description=stmt.excluded.description,
                video_url=stmt.excluded.video_url
            )
        )
        await session.execute(stmt)
        await session.commit()
    
    await message.answer("✅ Контент успешно сохранен в базу!")
    await state.clear()