from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# ВЫНОСИМ ФУНКЦИЮ СОЗДАНИЯ КЛАВИАТУРЫ ОТДЕЛЬНО
def get_games_menu_kb():
    """Возвращает клавиатуру меню игр"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🎮 Игры для 5-7 классов",
            callback_data="games_young"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎮 Игры для 9-11 классов",
            callback_data="games_teen"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎮 Игры для студентов",
            callback_data="games_student"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад в главное меню",
            callback_data="back_main_menu"
        )
    )
    
    return builder.as_markup()

# ХЕНДЛЕР ДЛЯ callback_data="menu_games" (если прилетает из бота)
@router.callback_query(F.data == "menu_games")
async def show_games_menu(callback: CallbackQuery):
    """Главное меню мини-игр (обработчик для callback)"""
    
    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "🎮 **Мини-игры**\n\n"
        "Выберите возрастную группу:",
        reply_markup=get_games_menu_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("games_"))
async def show_age_specific_games(callback: CallbackQuery):
    """Игры для конкретной возрастной группы"""
    age_group = callback.data.split("_")[1]  # young, teen, student
    
    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass

    builder = InlineKeyboardBuilder()
    
    if age_group == "young":
        # Игры для 5-7 классов
        builder.row(
            InlineKeyboardButton(
                text="♻️ Сортировка мусора",
                callback_data=f"game_waste_{age_group}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="👍 Правильные привычки",
                callback_data=f"game_habits_{age_group}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❓ Что правильно?",
                callback_data=f"game_rightwrong_{age_group}"
            )
        )
    else:
        # Для старших групп пока одна игра
        builder.row(
            InlineKeyboardButton(
                text="📖 Сюжетная игра",
                callback_data=f"game_story_{age_group}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к выбору возраста",
            callback_data="menu_games"
        )
    )
    
    age_names = {
        "young": "5-7 классы",
        "teen": "9-11 классы", 
        "student": "Студенты"
    }
    
    await callback.message.answer(
        f"🎮 Игры для **{age_names[age_group]}**\n\n"
        "Выберите игру:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()