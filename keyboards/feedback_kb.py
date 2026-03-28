from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_feedback_kb():
    """Клавиатура для обратной связи (3 критерия)"""
    builder = InlineKeyboardBuilder()
    
    # Полезность
    builder.row(InlineKeyboardButton(text="📊 Полезность:", callback_data="noop"))
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"usefulness_{i}"))
    builder.adjust(5)
    
    # Интерес
    builder.row(InlineKeyboardButton(text="🎯 Интерес:", callback_data="noop"))
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"interest_{i}"))
    builder.adjust(5)
    
    # Понятность
    builder.row(InlineKeyboardButton(text="💡 Понятность:", callback_data="noop"))
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"clarity_{i}"))
    builder.adjust(5)
    
    # Кнопка отправки
    builder.row(InlineKeyboardButton(text="✅ Отправить оценку", callback_data="submit_feedback"))
    
    return builder.as_markup()