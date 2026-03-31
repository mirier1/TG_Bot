from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.games_data import WASTE_ITEMS, WASTE_CATEGORIES
from .utils import save_game_result, create_game_keyboard, get_performance_text
from services.analytics import log_activity
import random
import asyncio

router = Router()

class WasteGameStates(StatesGroup):
    playing = State()

@router.callback_query(F.data.startswith("game_waste_"))
async def start_waste_game(callback: CallbackQuery, state: FSMContext):
    """Запуск игры 'Сортировка мусора'"""
    age_group = callback.data.split("_")[2]
    
    # Логирование игры
    await log_activity(
        user_id=callback.from_user.id,
        action="game_sorting",
        target_id=None,
        details=f"waste_sorting_{age_group}"
    )

    # Инициализация состояния
    await state.update_data(
        game_type="waste",
        age_group=age_group,
        score=0,
        step=0,
        total_steps=5
    )
    
    await ask_waste_question(callback, state)
    await callback.answer()

async def ask_waste_question(callback: CallbackQuery, state: FSMContext):
    """Задаёт вопрос по сортировке мусора"""
    data = await state.get_data()
    
    # Выбираем случайный предмет
    item_name = random.choice(list(WASTE_ITEMS.keys()))
    correct_category = WASTE_ITEMS[item_name]
    
    # Обновляем состояние
    await state.update_data(
        current_item=item_name,
        correct_category=correct_category,
        step=data["step"] + 1
    )
    
    # Создаём клавиатуру с вариантами
    builder = InlineKeyboardBuilder()
    categories = WASTE_CATEGORIES.copy()
    random.shuffle(categories)
    
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=category,
                callback_data=f"waste_answer_{category}"
            )
        )
    
    # Отправляем вопрос
    await callback.message.edit_text(
        f"♻️ **Сортировка мусора**\n\n"
        f"Вопрос {data['step'] + 1}/{data['total_steps']}\n"
        f"Счет: {data['score']}\n\n"
        f"Куда выбросить: **{item_name}**?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(WasteGameStates.playing)

@router.callback_query(WasteGameStates.playing, F.data.startswith("waste_answer_"))
async def handle_waste_answer(callback: CallbackQuery, state: FSMContext):
    selected_category = callback.data.replace("waste_answer_", "")
    data = await state.get_data()
    
    if selected_category == data["correct_category"]:
        data["score"] += 10
        result_text = f"✅ **Правильно!** {data['current_item']} — это {data['correct_category']}!"
    else:
        result_text = f"❌ **Неправильно!** {data['current_item']} — это {data['correct_category']}"
    
    await state.update_data(score=data["score"])
    
    if data["step"] < data["total_steps"]:
        # ПОКАЗЫВАЕМ КНОПКУ "ДАЛЕЕ" вместо ожидания
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="➡️ Далее",
                callback_data="waste_next_question"
            )
        )
        
        await callback.message.edit_text(
            result_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()
    else:
        await finish_waste_game(callback, state, result_text)

# ДОБАВЬ НОВЫЙ ХЕНДЛЕР ДЛЯ КНОПКИ "ДАЛЕЕ"
@router.callback_query(F.data == "waste_next_question")
async def next_waste_question(callback: CallbackQuery, state: FSMContext):
    """Переход к следующему вопросу по кнопке"""
    await ask_waste_question(callback, state)
    await callback.answer()

async def finish_waste_game(callback: CallbackQuery, state: FSMContext, result_text: str):
    """Завершение игры 'Сортировка мусора'"""
    data = await state.get_data()
    
    # Сохраняем результат
    max_score = data["total_steps"] * 10
    await save_game_result(
        user_id=callback.from_user.id,
        game_type="waste",
        age_group=data["age_group"],
        score=data["score"],
        max_score=max_score,
        steps=data["total_steps"]
    )
    
    # Создаём финальное сообщение
    percentage = (data["score"] / max_score) * 100
    performance = get_performance_text(data["score"], max_score)
    
    await callback.message.edit_text(
        f"{result_text}\n\n"
        f"🎮 **Игра завершена!**\n\n"
        f"📊 Результат: {data['score']}/{max_score} очков\n"
        f"📈 Процент: {percentage:.0f}%\n"
        f"🏅 {performance}\n\n"
        f"Что дальше?",
        reply_markup=create_game_keyboard(data["age_group"], "waste"),
        parse_mode="Markdown"
    )
    
    await state.clear()