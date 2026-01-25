from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_kb():
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📚 Цели устойчивого развития", callback_data="menu_sdg"),
        InlineKeyboardButton(text="🎮 Мини-игры", callback_data="menu_games"),
    )
    
    builder.row(
        InlineKeyboardButton(text="❓ Вопрос эксперту", callback_data="menu_question"),
        InlineKeyboardButton(text="🎓 Стать посланником", callback_data="menu_ambassador"),
    )
    
    builder.row(
        InlineKeyboardButton(text="🎥 Конкурс «Я есть ЦУР»", callback_data="menu_contest"),
        InlineKeyboardButton(text="📊 Обратная связь", callback_data="menu_feedback"),
    )
    
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки профиля", callback_data="menu_settings"),
    )
    
    return builder.as_markup()