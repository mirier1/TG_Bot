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
    """Клавиатура с вариантами ответа для вопроса (без доп. кнопок)"""
    builder = InlineKeyboardBuilder()
    for opt in options:
        builder.add(InlineKeyboardButton(
            text=f"{opt['label']}) {opt['text'][:50]}...",
            callback_data=f"story_opt_{opt['label']}"
        ))
    builder.adjust(1)
    return builder.as_markup()

def story_stats_kb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой просмотра статов"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📊 Показать статы", callback_data="story_show_stats"))
    return builder.as_markup()

def story_game_kb() -> InlineKeyboardMarkup:
    """Клавиатура с игровыми действиями (сохранить, выйти)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💾 Сохранить", callback_data="story_save"),
        InlineKeyboardButton(text="🚪 Выйти", callback_data="story_quit")
    )
    return builder.as_markup()

def story_continue_kb() -> InlineKeyboardMarkup:
    """Клавиатура для продолжения игры"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="▶️ Продолжить", callback_data="story_continue"),
        InlineKeyboardButton(text="🔄 Начать заново", callback_data="story_new"),
        InlineKeyboardButton(text="🗑️ Удалить сохранение", callback_data="story_delete_save")
    )
    return builder.as_markup()