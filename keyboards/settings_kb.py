from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_settings_kb():
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить возраст", callback_data="settings_change_age"),
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_main_menu"),
    )
    
    return builder.as_markup()