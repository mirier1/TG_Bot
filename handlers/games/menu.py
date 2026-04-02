from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_games_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎮 Игры для 1-8 классов", callback_data="games_1_8"))
    builder.row(InlineKeyboardButton(text="📖 Сюжетная игра (9-11 классы)", callback_data="game_story"))
    builder.row(InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_main_menu"))
    return builder.as_markup()

@router.callback_query(F.data == "menu_games")
async def show_games_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "🎮 **Мини-игры**\n\nВыберите режим:",
        reply_markup=get_games_menu_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "games_1_8")
async def show_games_for_1_8(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="♻️ Сортировка мусора", callback_data="game_waste_1_8"))
    builder.row(InlineKeyboardButton(text="👍 Правильные привычки", callback_data="game_habits_1_8"))
    builder.row(InlineKeyboardButton(text="❓ Что правильно?", callback_data="game_rightwrong_1_8"))
    builder.row(InlineKeyboardButton(text="◀️ Назад к выбору режима", callback_data="menu_games"))

    await callback.message.answer(
        "🎮 **Игры для 1-8 классов**\n\nВыберите игру:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()