from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_rating_kb(prefix: str):
    """Клавиатура для оценки 1-5"""
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(
            text=str(i), 
            callback_data=f"{prefix}_{i}"
        ))
    builder.adjust(5)
    return builder.as_markup()

def get_comment_kb():
    """Клавиатура для комментария"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💬 Оставить комментарий", callback_data="feedback_comment"),
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="feedback_skip")
    )
    return builder.as_markup()