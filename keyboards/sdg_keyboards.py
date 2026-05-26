from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.constants import SDG_TITLES

SHORT_SDG_TITLES = {
    1: "Ликвидация нищеты",
    2: "Ликвидация голода",
    3: "Здоровье и благополучие",
    4: "Качественное образование",
    5: "Гендерное равенство",
    6: "Чистая вода и санитария",
    7: "Чистая энергия",
    8: "Достойная работа и рост",
    9: "Индустриализация и инновации",
    10: "Снижение неравенства",
    11: "Устойчивые города",
    12: "Ответственное потребление",
    13: "Борьба с климатом",
    14: "Сохранение океанов",
    15: "Сохранение экосистем суши",
    16: "Мир и правосудие",
    17: "Партнёрство для целей",
}

def get_sdg_list_kb():
    """Клавиатура со списком 17 ЦУР (с краткими названиями)"""
    builder = InlineKeyboardBuilder()

    for num in range(1, 18):
        builder.add(InlineKeyboardButton(
            text=f"{num}. {SHORT_SDG_TITLES[num]}",
            callback_data=f"sdg_{num}"
        ))

    builder.adjust(1)  # по одной кнопке в строке
    builder.row(InlineKeyboardButton(
        text="◀️ Назад в меню",
        callback_data="back_to_main_menu"
    ))

    return builder.as_markup()


def get_sdg_detail_kb(sdg_num: int):
    """Клавиатура внутри карточки ЦУР"""
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