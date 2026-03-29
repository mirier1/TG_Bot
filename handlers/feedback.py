from aiogram import Router, F
from aiogram.types import CallbackQuery, PollAnswer
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram import Bot

from database import AsyncSessionLocal
from models import Feedback
from utils.constants import SDG_TITLES

router = Router()

class FeedbackStates(StatesGroup):
    usefulness = State()
    interest = State()
    clarity = State()

# Временное хранилище
user_feedback = {}  # user_id -> {"sdg_id": x, "usefulness": x, ...}

@router.callback_query(F.data.startswith("rate_"))
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    sdg_num = int(callback.data.split("_")[1])
    await state.update_data(sdg_id=sdg_num)
    user_feedback[callback.from_user.id] = {"sdg_id": sdg_num}
    await state.set_state(FeedbackStates.usefulness)
    
    await callback.message.answer_poll(
        question=f"📊 Оцените **полезность** лекции по ЦУР {sdg_num}:",
        options=["5 - Отлично", "4 - Хорошо", "3 - Средне", "2 - Плохо", "1 - Ужасно"],
        is_anonymous=False,
        allows_multiple_answers=False
    )
    await callback.answer()

@router.poll_answer()
async def handle_poll(poll_answer: PollAnswer, state: FSMContext, bot: Bot):
    user_id = poll_answer.user.id
    option_id = poll_answer.option_ids[0] if poll_answer.option_ids else None
    rating = 5 - option_id if option_id is not None else None
    
    current_state = await state.get_state()
    
    if current_state == FeedbackStates.usefulness.state:
        await state.update_data(usefulness=rating)
        user_feedback[user_id]["usefulness"] = rating
        await state.set_state(FeedbackStates.interest)
        
        await bot.send_poll(
            user_id,
            question="📊 Оцените **интересность** лекции:",
            options=["5 - Отлично", "4 - Хорошо", "3 - Средне", "2 - Плохо", "1 - Ужасно"],
            is_anonymous=False,
            allows_multiple_answers=False
        )
        
    elif current_state == FeedbackStates.interest.state:
        await state.update_data(interest=rating)
        user_feedback[user_id]["interest"] = rating
        await state.set_state(FeedbackStates.clarity)
        
        await bot.send_poll(
            user_id,
            question="📊 Оцените **понятность** лекции:",
            options=["5 - Отлично", "4 - Хорошо", "3 - Средне", "2 - Плохо", "1 - Ужасно"],
            is_anonymous=False,
            allows_multiple_answers=False
        )
        
    elif current_state == FeedbackStates.clarity.state:
        await state.update_data(clarity=rating)
        user_feedback[user_id]["clarity"] = rating
        
        # Сохраняем в БД
        data = await state.get_data()
        async with AsyncSessionLocal() as session:
            feedback = Feedback(
                user_id=user_id,
                sdg_id=data.get("sdg_id"),
                usefulness=data.get("usefulness"),
                interest=data.get("interest"),
                clarity=rating
            )
            session.add(feedback)
            await session.commit()
        
        # Показываем результат и кнопку назад
        from keyboards.sdg_keyboards import get_sdg_detail_kb
        
        await bot.send_message(
            user_id,
            f"✅ **Спасибо за обратную связь!**\n\n"
            f"Ваши оценки по ЦУР {data.get('sdg_id')} сохранены.\n\n"
            f"Вернуться к лекции:",
            reply_markup=get_sdg_detail_kb(data.get("sdg_id")),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Очистка
        await state.clear()
        if user_id in user_feedback:
            del user_feedback[user_id]