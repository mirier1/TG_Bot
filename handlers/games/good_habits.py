from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.games_data import GOOD_HABITS
from .utils import save_game_result, create_game_keyboard, get_performance_text
import random
import asyncio

router = Router()

class HabitsGameStates(StatesGroup):
    playing = State()

@router.callback_query(F.data.startswith("game_habits_"))
async def start_habits_game(callback: CallbackQuery, state: FSMContext):
    """Запуск игры 'Правильные привычки'"""
    age_group = callback.data.split("_")[2]
    
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
    """Задаёт вопрос по привычкам"""
    data = await state.get_data()
    
    # Выбираем случайную привычку
    habit, is_good = random.choice(GOOD_HABITS)
    
    await state.update_data(
        current_habit=habit,
        correct_is_good=is_good,
        step=data["step"] + 1
    )
    
    # Создаём клавиатуру
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
    """Обработка ответа в игре с привычками"""
    user_choice = callback.data.replace("habits_answer_", "")  # "good" или "bad"
    data = await state.get_data()
    
    # Проверяем ответ
    user_is_good = (user_choice == "good")
    correct_is_good = data["correct_is_good"]
    
    if user_is_good == correct_is_good:
        data["score"] += 10
        result_text = f"✅ **Правильно!** Это {'хорошая' if correct_is_good else 'плохая'} привычка!"
    else:
        result_text = f"❌ **Неправильно!** Это {'хорошая' if correct_is_good else 'плохая'} привычка!"
    
    await state.update_data(score=data["score"])
    
    if data["step"] < data["total_steps"]:
        # Следующий вопрос
        await callback.message.edit_text(result_text)
        await callback.answer()
        await asyncio.sleep(1.5)
        await ask_habits_question(callback, state)
    else:
        # Конец игры
        await finish_habits_game(callback, state, result_text)

async def finish_habits_game(callback: CallbackQuery, state: FSMContext, result_text: str):
    """Завершение игры 'Правильные привычки'"""
    data = await state.get_data()
    
    # Сохраняем результат
    max_score = data["total_steps"] * 10
    await save_game_result(
        user_id=callback.from_user.id,
        game_type="habits",
        age_group=data["age_group"],
        score=data["score"],
        max_score=max_score,
        steps=data["total_steps"]
    )
    
    # Финальное сообщение
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