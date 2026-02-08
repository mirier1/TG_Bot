from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.constants import SDG_TITLES

def get_sdg_list_kb():
    """Клавиатура со списком 17 ЦУР"""
    builder = InlineKeyboardBuilder()
    
    for num, title in SDG_TITLES.items():
        short_title = title[:30] + "..." if len(title) > 30 else title
        builder.add(InlineKeyboardButton(
            text=f"{num}. {short_title}",
            callback_data=f"sdg_{num}"
        ))
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(
        text="◀️ Назад в меню",
        callback_data="back_to_main_menu"
    ))
    
    return builder.as_markup()

def get_sdg_detail_kb(sdg_num: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Пройти квиз", callback_data=f"quiz_{sdg_num}")],
        [InlineKeyboardButton(text="🎥 Видео", callback_data=f"video_{sdg_num}")],
        [InlineKeyboardButton(text="📖 Подробнее", callback_data=f"more_{sdg_num}")],
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_sdg_list")]
    ])