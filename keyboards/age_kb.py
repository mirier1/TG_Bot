from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_age_kb():
    """Inline-клавиатура для выбора возрастной группы"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="5-7 класс", callback_data="age_young"),
        InlineKeyboardButton(text="9-11 класс", callback_data="age_teen"),
    )
    
    builder.row(
        InlineKeyboardButton(text="Студент", callback_data="age_student"),
    )
    
    return builder.as_markup()