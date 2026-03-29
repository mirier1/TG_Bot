from aiogram import Router, F
from aiogram.types import CallbackQuery, PollAnswer
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram import Bot

from database import AsyncSessionLocal
from models import Feedback
from utils.constants import SDG_TITLES
from keyboards.sdg_keyboards import get_sdg_back_kb

router = Router()

class FeedbackStates(StatesGroup):
    usefulness = State()
    interest = State()
    clarity = State()

# Временное хранилище
user_feedback = {}  # user_id -> {"sdg_id": x, "usefulness": x, ...}

@router.callback_query(F.data.startswith("rate_"))
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    """Запуск первого опроса"""
    sdg_num = int(callback.data.split("_")[1])
    
    await state.update_data(sdg_id=sdg_num)
    user_feedback[callback.from_user.id] = {"sdg_id": sdg_num}
    await state.set_state(FeedbackStates.usefulness)
    
    # Отправляем первый опрос
    msg = await callback.message.answer_poll(
        question=f"📊 Оцените **полезность** лекции по ЦУР {sdg_num}:",
        options=["5 - Отлично", "4 - Хорошо", "3 - Средне", "2 - Плохо", "1 - Ужасно"],
        is_anonymous=False,
        allows_multiple_answers=False
    )
    
    # Сохраняем ID сообщения с опросом для удаления
    await state.update_data(poll_message_id=msg.message_id)
    
    # Удаляем исходное сообщение с кнопкой "Оценить лекцию"
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.answer()

@router.poll_answer()
async def handle_poll(poll_answer: PollAnswer, state: FSMContext, bot: Bot):
    """Обработка ответов на опросы"""
    user_id = poll_answer.user.id
    option_id = poll_answer.option_ids[0] if poll_answer.option_ids else None
    rating = 5 - option_id if option_id is not None else None
    
    current_state = await state.get_state()
    data = await state.get_data()
    
    # Удаляем сообщение с опросом
    try:
        await bot.delete_message(user_id, data.get("poll_message_id"))
    except:
        pass
    
    if current_state == FeedbackStates.usefulness.state:
        await state.update_data(usefulness=rating)
        if user_id in user_feedback:
            user_feedback[user_id]["usefulness"] = rating
        await state.set_state(FeedbackStates.interest)
        
        # Второй опрос
        msg = await bot.send_poll(
            user_id,
            question="📊 Оцените **интересность** лекции:",
            options=["5 - Отлично", "4 - Хорошо", "3 - Средне", "2 - Плохо", "1 - Ужасно"],
            is_anonymous=False,
            allows_multiple_answers=False
        )
        await state.update_data(poll_message_id=msg.message_id)
        
    elif current_state == FeedbackStates.interest.state:
        await state.update_data(interest=rating)
        if user_id in user_feedback:
            user_feedback[user_id]["interest"] = rating
        await state.set_state(FeedbackStates.clarity)
        
        # Третий опрос
        msg = await bot.send_poll(
            user_id,
            question="📊 Оцените **понятность** лекции:",
            options=["5 - Отлично", "4 - Хорошо", "3 - Средне", "2 - Плохо", "1 - Ужасно"],
            is_anonymous=False,
            allows_multiple_answers=False
        )
        await state.update_data(poll_message_id=msg.message_id)
        
    elif current_state == FeedbackStates.clarity.state:
        await state.update_data(clarity=rating)
        
        # Получаем все данные
        data = await state.get_data()
        sdg_id = data.get("sdg_id")
        usefulness = data.get("usefulness")
        interest = data.get("interest")
        
        # Сохраняем в БД
        async with AsyncSessionLocal() as session:
            feedback = Feedback(
                user_id=user_id,
                sdg_id=sdg_id,
                usefulness=usefulness,
                interest=interest,
                clarity=rating
            )
            session.add(feedback)
            await session.commit()
        
        # Отправляем сообщение с результатом и кнопкой назад
        await bot.send_message(
            user_id,
            f"✅ **Спасибо за обратную связь!**\n\n"
            f"Ваши оценки по ЦУР {sdg_id} сохранены.",
            reply_markup=get_sdg_back_kb(sdg_id),  # ← новая кнопка
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Очистка
        await state.clear()
        if user_id in user_feedback:
            del user_feedback[user_id]