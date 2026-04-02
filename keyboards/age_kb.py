from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_age_kb():
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="1-4 класс", callback_data="age_1_4"),
        InlineKeyboardButton(text="5-8 класс", callback_data="age_5_8"),
        InlineKeyboardButton(text="9-11 класс", callback_data="age_9_11"),
    )
    
    return builder.as_markup()