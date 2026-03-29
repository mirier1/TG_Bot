from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_games_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎮 Игры для 5-7 классов", callback_data="games_young")
    )
    builder.row(
        InlineKeyboardButton(text="🎮 Игры для 9-11 классов", callback_data="games_teen")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_main_menu")
    )
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
    age_group = callback.data.split("_")[1]
    try:
        await callback.message.delete()
    except:
        pass

    builder = InlineKeyboardBuilder()
    if age_group == "young":
        builder.row(InlineKeyboardButton(text="♻️ Сортировка мусора", callback_data="game_waste_young"))
        builder.row(InlineKeyboardButton(text="👍 Правильные привычки", callback_data="game_habits_young"))
        builder.row(InlineKeyboardButton(text="❓ Что правильно?", callback_data="game_rightwrong_young"))
    else:
        # для 9-11 классов — одна сюжетная игра
        builder.row(InlineKeyboardButton(text="📖 Сюжетная игра", callback_data="game_story"))

    builder.row(InlineKeyboardButton(text="◀️ Назад к выбору возраста", callback_data="menu_games"))

    age_names = {"young": "5-7 классы", "teen": "9-11 классы"}
    await callback.message.answer(
        f"🎮 Игры для **{age_names[age_group]}**\n\nВыберите игру:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()