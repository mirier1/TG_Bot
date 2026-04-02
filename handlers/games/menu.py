from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_games_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎮 Игры для 1-4 классов", callback_data="games_1_4"))
    builder.row(InlineKeyboardButton(text="🎮 Игры для 5-8 классов", callback_data="games_5_8"))
    builder.row(InlineKeyboardButton(text="🎮 Игры для 9-11 классов", callback_data="games_9_11"))
    builder.row(InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_main_menu"))
    return builder.as_markup()

@router.callback_query(F.data == "menu_games")
async def show_games_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "🎮 **Мини-игры**\n\nВыберите возрастную группу:",
        reply_markup=get_games_menu_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("games_"))
async def show_age_specific_games(callback: CallbackQuery):
    age_group = callback.data.split("_")[1]  # '1_4', '5_8', '9_11'
    age_display = {"1_4": "1-4 классы", "5_8": "5-8 классы", "9_11": "9-11 классы"}
    try:
        await callback.message.delete()
    except:
        pass

    builder = InlineKeyboardBuilder()
    if age_group in ("1_4", "5_8"):
        builder.row(InlineKeyboardButton(text="♻️ Сортировка мусора", callback_data=f"game_waste_{age_group}"))
        builder.row(InlineKeyboardButton(text="👍 Правильные привычки", callback_data=f"game_habits_{age_group}"))
        builder.row(InlineKeyboardButton(text="❓ Что правильно?", callback_data=f"game_rightwrong_{age_group}"))
    else:  # 9_11
        builder.row(InlineKeyboardButton(text="📖 Сюжетная игра", callback_data="game_story"))

    builder.row(InlineKeyboardButton(text="◀️ Назад к выбору возраста", callback_data="menu_games"))

    await callback.message.answer(
        f"🎮 Игры для **{age_display[age_group]}**\n\nВыберите игру:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()