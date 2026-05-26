from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.constants import SHORT_SDG_TITLES

def get_sdg_list_kb():
    """Reply-клавиатура со списком ЦУР (текст слева)"""
    buttons = []
    for num in range(1, 18):
        buttons.append([KeyboardButton(text=SHORT_SDG_TITLES[num])])
    buttons.append([KeyboardButton(text="◀️ Назад в меню")])
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_sdg_detail_kb(sdg_num: int):
    """Клавиатура внутри карточки ЦУР (inline)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Пройти квиз", callback_data=f"quiz_{sdg_num}")],
        [InlineKeyboardButton(text="🎥 Видео", callback_data=f"video_{sdg_num}")],
        [InlineKeyboardButton(text="📖 Подробнее", callback_data=f"more_{sdg_num}")],
        [InlineKeyboardButton(text="📊 Оценить лекцию", callback_data=f"rate_{sdg_num}")],
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_sdg_list")]
    ])


def get_sdg_back_kb(sdg_num: int):
    """Клавиатура только с кнопкой 'Вернуться к лекции' (без квиза)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Вернуться к лекции", callback_data=f"back_to_sdg_{sdg_num}")]
    ])