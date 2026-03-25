from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from database import AsyncSessionLocal
from models import Feedback
from handlers.states.feedback_states import FeedbackStates
from keyboards.feedback_kb import get_rating_kb, get_comment_kb
from keyboards.main_menu_kb import get_main_kb

router = Router()

# Запуск обратной связи (вызывается из главного меню или после квиза)
@router.callback_query(F.data == "menu_feedback")
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FeedbackStates.usefulness)
    await callback.message.answer(
        "📊 **Обратная связь**\n\n"
        "Помогите нам стать лучше! Оцените по шкале 1-5:\n\n"
        "1️⃣ Оцените **полезность** материала:",
        reply_markup=get_rating_kb("usefulness"),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

# Обработка оценки полезности
@router.callback_query(F.data.startswith("usefulness_"))
async def process_usefulness(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(usefulness=rating)
    await state.set_state(FeedbackStates.interest)
    
    await callback.message.edit_text(
        "📊 **Обратная связь**\n\n"
        "2️⃣ Оцените **интересность** материала:",
        reply_markup=get_rating_kb("interest"),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

# Обработка оценки интереса
@router.callback_query(F.data.startswith("interest_"))
async def process_interest(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(interest=rating)
    await state.set_state(FeedbackStates.clarity)
    
    await callback.message.edit_text(
        "📊 **Обратная связь**\n\n"
        "3️⃣ Оцените **понятность** материала:",
        reply_markup=get_rating_kb("clarity"),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

# Обработка оценки понятности
@router.callback_query(F.data.startswith("clarity_"))
async def process_clarity(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(clarity=rating)
    await state.set_state(FeedbackStates.comment)
    
    await callback.message.edit_text(
        "📊 **Обратная связь**\n\n"
        "Хотите оставить комментарий?",
        reply_markup=get_comment_kb(),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

# Обработка комментария
@router.callback_query(F.data == "feedback_comment")
async def ask_comment(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Напишите ваш комментарий (или /skip чтобы пропустить):",
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.message(FeedbackStates.comment)
async def process_comment(message: Message, state: FSMContext):
    if message.text == "/skip":
        await save_feedback(message, state, comment=None)
    else:
        await save_feedback(message, state, comment=message.text)

# Пропуск комментария
@router.callback_query(F.data == "feedback_skip")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await save_feedback(callback, state, comment=None)
    await callback.answer()

# Сохранение и завершение
async def save_feedback(update, state: FSMContext, comment=None):
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        feedback = Feedback(
            user_id=update.from_user.id,
            sdg_id=None,  # Пока без привязки к ЦУР
            usefulness=data["usefulness"],
            interest=data["interest"],
            clarity=data["clarity"],
            comment=comment
        )
        session.add(feedback)
        await session.commit()
    
    if isinstance(update, Message):
        await update.answer(
            "✅ **Спасибо за обратную связь!**\n\n"
            "Ваше мнение помогает нам становиться лучше!",
            reply_markup=get_main_kb(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.edit_text(
            "✅ **Спасибо за обратную связь!**\n\n"
            "Ваше мнение помогает нам становиться лучше!",
            reply_markup=get_main_kb(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    await state.clear()