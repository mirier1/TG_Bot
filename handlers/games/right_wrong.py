from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.games_data import RIGHT_WRONG_SCENARIOS
from .utils import save_game_result, create_game_keyboard, get_performance_text
from services.analytics import log_activity
import random
import asyncio

router = Router()

class RightWrongGameStates(StatesGroup):
    playing = State()

@router.callback_query(F.data.startswith("game_rightwrong_"))
async def start_rightwrong_game(callback: CallbackQuery, state: FSMContext):
    """Запуск игры 'Что правильно?'"""
    age_group = callback.data.split("_")[2]
    
    #Логирование игры
    await log_activity(
        user_id=callback.from_user.id,
        action="game_right_wrong",
        target_id=None,
        details=f"right_wrong_{age_group}"
    )

    await state.update_data(
        game_type="rightwrong",
        age_group=age_group,
        score=0,
        step=0,
        total_steps=3,
        used_scenarios=[]
    )
    
    await ask_rightwrong_question(callback, state)
    await callback.answer()

async def ask_rightwrong_question(callback: CallbackQuery, state: FSMContext):
    """Задаёт вопрос сценария"""
    data = await state.get_data()
    
    # Выбираем сценарий, который ещё не использовался
    available_scenarios = [s for s in RIGHT_WRONG_SCENARIOS 
                          if s not in data.get("used_scenarios", [])]
    
    if not available_scenarios:
        # Если все сценарии использованы, перемешиваем заново
        await state.update_data(used_scenarios=[])
        available_scenarios = RIGHT_WRONG_SCENARIOS.copy()
    
    scenario, answers = random.choice(available_scenarios)
    
    # Обновляем состояние
    data["used_scenarios"].append((scenario, answers))
    await state.update_data(
        current_scenario=scenario,
        current_answers=answers,
        step=data["step"] + 1,
        used_scenarios=data["used_scenarios"]
    )
    
    # Создаём клавиатуру с вариантами (используем индексы для callback_data)
    builder = InlineKeyboardBuilder()
    for i, (answer_text, points) in enumerate(answers.items()):
        # Используем индекс вместо текста для callback_data
        callback_data = f"rightwrong_answer_{i}"
        
        builder.row(
            InlineKeyboardButton(
                text=answer_text,
                callback_data=callback_data
            )
        )
    
    await callback.message.answer(
        f"❓ **Что правильно?**\n\n"
        f"Ситуация {data['step'] + 1}/{data['total_steps']}\n"
        f"Счет: {data['score']}\n\n"
        f"**{scenario}**",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(RightWrongGameStates.playing)

@router.callback_query(RightWrongGameStates.playing, F.data.startswith("rightwrong_answer_"))
async def handle_rightwrong_answer(callback: CallbackQuery, state: FSMContext):
    answer_index = int(callback.data.replace("rightwrong_answer_", ""))
    data = await state.get_data()
    
    answers = data["current_answers"]
    answer_items = list(answers.items())
    answer_text, points = answer_items[answer_index]
    
    data["score"] += points
    
    if points > 0:
        result_text = f"✅ **Отличный выбор!** +{points} очков!"
    elif points == 0:
        result_text = "😐 Можно было бы и лучше..."
    else:
        result_text = f"❌ **Не самый лучший вариант...** {points} очков"
    
    await state.update_data(score=data["score"])
    
    if data["step"] < data["total_steps"]:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="➡️ Далее",
                callback_data="rightwrong_next_question"
            )
        )
        
        await callback.message.edit_text(
            result_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()
    else:
        await finish_rightwrong_game(callback, state, result_text)

@router.callback_query(F.data == "rightwrong_next_question")
async def next_rightwrong_question(callback: CallbackQuery, state: FSMContext):
    await ask_rightwrong_question(callback, state)
    await callback.answer()

async def finish_rightwrong_game(callback: CallbackQuery, state: FSMContext, result_text: str):
    """Завершение игры 'Что правильно?'"""
    data = await state.get_data()
    
    # Максимальный возможный счёт (все ответы по +10)
    max_score = data["total_steps"] * 10
    
    # Сохраняем результат
    await save_game_result(
        user_id=callback.from_user.id,
        game_type="rightwrong",
        age_group=data["age_group"],
        score=data["score"],
        max_score=max_score,
        steps=data["total_steps"]
    )
    
    # Финальное сообщение
    percentage = (data["score"] / max_score) * 100 if max_score > 0 else 0
    performance = get_performance_text(data["score"], max_score)
    
    await callback.message.answer(
        f"{result_text}\n\n"
        f"🎮 **Игра завершена!**\n\n"
        f"📊 Результат: {data['score']}/{max_score} очков\n"
        f"📈 Процент: {percentage:.0f}%\n"
        f"🏅 {performance}\n\n"
        f"Что дальше?",
        reply_markup=create_game_keyboard(data["age_group"], "rightwrong"),
        parse_mode="Markdown"
    )
    
    await state.clear()