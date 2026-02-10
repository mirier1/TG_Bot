from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from keyboards.main_menu_kb import get_main_kb

router = Router()

@router.callback_query(F.data == "back_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "help_games")
async def show_games_help(callback: CallbackQuery):
    """Показывает справку по играм"""
    help_text = (
        "🎮 Помощь по мини-играм\n\n"
        "Игры для 5-7 классов:\n"
        "• ♻️ Сортировка мусора — учимся правильно сортировать отходы\n"
        "• 👍 Правильные привычки — определяем хорошие и плохие привычки\n"
        "• ❓ Что правильно? — выбираем правильное поведение в ситуациях\n\n"
        "Игры для 9-11 классов и студентов:\n"
        "• 📖 Сюжетная игра — принимаем решения в сложных ситуациях\n\n"
        "Как играть:\n"
        "1. Выберите возрастную группу\n"
        "2. Выберите игру\n"
        "3. Отвечайте на вопросы\n"
        "4. Набирайте очки за правильные ответы\n\n"
        "Результаты сохраняются в вашем профиле!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu_games")
    )
    
    await callback.message.answer(
        help_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()