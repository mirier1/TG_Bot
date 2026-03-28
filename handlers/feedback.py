from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from database import AsyncSessionLocal
from models import Feedback
from handlers.states.feedback_states import FeedbackStates
from keyboards.feedback_kb import get_feedback_kb
from utils.constants import SDG_TITLES

router = Router()

# Временное хранилище для выбранных оценок
user_ratings = {}  # user_id -> {"usefulness": x, "interest": y, "clarity": z}

@router.callback_query(F.data.startswith("rate_"))
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    """Запуск формы обратной связи"""
    sdg_num = int(callback.data.split("_")[1])
    sdg_title = SDG_TITLES.get(sdg_num, f"ЦУР {sdg_num}")
    
    # Сохраняем sdg_id
    await state.update_data(sdg_id=sdg_num)
    user_ratings[callback.from_user.id] = {}
    
    await callback.message.answer(
        f"📊 **Обратная связь**\n\n"
        f"Оцените лекцию по ЦУР {sdg_num}:\n"
        f"_{sdg_title[:50]}..._\n\n"
        f"Выберите оценки 1-5:",
        reply_markup=get_feedback_kb(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await state.set_state(FeedbackStates.waiting_feedback)
    await callback.answer()

@router.callback_query(F.data.startswith("usefulness_"))
async def set_usefulness(callback: CallbackQuery):
    rating = int(callback.data.split("_")[1])
    user_ratings[callback.from_user.id]["usefulness"] = rating
    await callback.answer(f"✅ Полезность: {rating}")

@router.callback_query(F.data.startswith("interest_"))
async def set_interest(callback: CallbackQuery):
    rating = int(callback.data.split("_")[1])
    user_ratings[callback.from_user.id]["interest"] = rating
    await callback.answer(f"✅ Интерес: {rating}")

@router.callback_query(F.data.startswith("clarity_"))
async def set_clarity(callback: CallbackQuery):
    rating = int(callback.data.split("_")[1])
    user_ratings[callback.from_user.id]["clarity"] = rating
    await callback.answer(f"✅ Понятность: {rating}")

@router.callback_query(F.data == "submit_feedback")
async def submit_feedback(callback: CallbackQuery, state: FSMContext):
    """Сохранение обратной связи"""
    ratings = user_ratings.get(callback.from_user.id, {})
    
    usefulness = ratings.get("usefulness")
    interest = ratings.get("interest")
    clarity = ratings.get("clarity")
    
    if None in (usefulness, interest, clarity):
        await callback.answer("❌ Оцените все три критерия!", show_alert=True)
        return
    
    data = await state.get_data()
    sdg_id = data.get("sdg_id")
    
    async with AsyncSessionLocal() as session:
        feedback = Feedback(
            user_id=callback.from_user.id,
            sdg_id=sdg_id,
            usefulness=usefulness,
            interest=interest,
            clarity=clarity
        )
        session.add(feedback)
        await session.commit()
    
    # Очистка
    if callback.from_user.id in user_ratings:
        del user_ratings[callback.from_user.id]
    await state.clear()
    
    await callback.message.edit_text(
        "✅ **Спасибо за обратную связь!**\n\n"
        "Ваши оценки помогут нам улучшить материалы.",
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()