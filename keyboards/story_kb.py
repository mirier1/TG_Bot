from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def story_next_kb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Далее'"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Далее ➡️", callback_data="story_next"))
    return builder.as_markup()

def story_end_kb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Конец'"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔚 Конец", callback_data="story_end"))
    return builder.as_markup()

def story_options_kb(options: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура с вариантами ответа для вопроса"""
    builder = InlineKeyboardBuilder()
    for opt in options:
        builder.add(InlineKeyboardButton(
            text=f"{opt['label']}) {opt['text'][:50]}...",
            callback_data=f"story_opt_{opt['label']}"
        ))
    builder.adjust(1)
    return builder.as_markup()