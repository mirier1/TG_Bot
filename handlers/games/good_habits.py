from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.games_data import GOOD_HABITS
from .utils import save_game_result, create_game_keyboard, get_performance_text
from services.analytics import log_activity
import random

router = Router()

class HabitsGameStates(StatesGroup):
    playing = State()

@router.callback_query(F.data.startswith("game_habits_"))
async def start_habits_game(callback: CallbackQuery, state: FSMContext):
    age_group = callback.data.split("_")[2]  # '1_8'
    
    await log_activity(
        user_id=callback.from_user.id,
        action="game",
        target_id=None,
        details=f"habits_{age_group}"
    )

    await state.update_data(
        game_type="habits",
        age_group=age_group,
        score=0,
        step=0,
        total_steps=5
    )
    
    await ask_habits_question(callback, state)
    await callback.answer()

async def ask_habits_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    habit, is_good = random.choice(GOOD_HABITS)
    
    await state.update_data(
        current_habit=habit,
        correct_is_good=is_good,
        step=data["step"] + 1
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Это хорошая привычка",
            callback_data="habits_answer_good"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Это плохая привычка",
            callback_data="habits_answer_bad"
        )
    )
    
    await callback.message.edit_text(
        f"👍 **Правильные привычки**\n\n"
        f"Вопрос {data['step'] + 1}/{data['total_steps']}\n"
        f"Счет: {data['score']}\n\n"
        f"Привычка: **{habit}**\n\n"
        f"Это хорошая или плохая привычка?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(HabitsGameStates.playing)

@router.callback_query(HabitsGameStates.playing, F.data.startswith("habits_answer_"))
async def handle_habits_answer(callback: CallbackQuery, state: FSMContext):
    user_choice = callback.data.replace("habits_answer_", "")
    data = await state.get_data()
    
    user_is_good = (user_choice == "good")
    correct_is_good = data["correct_is_good"]
    
    if user_is_good == correct_is_good:
        data["score"] += 10
        result_text = f"✅ **Правильно!** Это {'хорошая' if correct_is_good else 'плохая'} привычка!"
    else:
        result_text = f"❌ **Неправильно!** Это {'хорошая' if correct_is_good else 'плохая'} привычка!"
    
    await state.update_data(score=data["score"])
    
    if data["step"] < data["total_steps"]:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="➡️ Далее",
                callback_data="habits_next_question"
            )
        )
        
        await callback.message.edit_text(
            result_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()
    else:
        await finish_habits_game(callback, state, result_text)

@router.callback_query(F.data == "habits_next_question")
async def next_habits_question(callback: CallbackQuery, state: FSMContext):
    await ask_habits_question(callback, state)
    await callback.answer()

async def finish_habits_game(callback: CallbackQuery, state: FSMContext, result_text: str):
    data = await state.get_data()
    
    max_score = data["total_steps"] * 10
    await save_game_result(
        user_id=callback.from_user.id,
        game_type="habits",
        age_group=data["age_group"],
        score=data["score"],
        max_score=max_score,
        steps=data["total_steps"]
    )
    
    percentage = (data["score"] / max_score) * 100
    performance = get_performance_text(data["score"], max_score)
    
    await callback.message.edit_text(
        f"{result_text}\n\n"
        f"🎮 **Игра завершена!**\n\n"
        f"📊 Результат: {data['score']}/{max_score} очков\n"
        f"📈 Процент: {percentage:.0f}%\n"
        f"🏅 {performance}\n\n"
        f"Что дальше?",
        reply_markup=create_game_keyboard(data["age_group"], "habits"),
        parse_mode="Markdown"
    )
    
    await state.clear()