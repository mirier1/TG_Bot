from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.constants import SDG_TITLES
from keyboards.main_menu_kb import get_main_kb

router = Router()

# Показ списка ЦУР
@router.message(F.text == "📚 Цели устойчивого развития")
@router.callback_query(F.data == "menu_sdg")
async def show_sdg_list(update: Message | CallbackQuery): #Показывает список 17 ЦУР. Принимает как Message, так и CallbackQuery
    if isinstance(update, CallbackQuery):
        message = update.message
        await update.answer()
        await message.delete()
    else:
        message = update
    
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
    
    await message.answer(
        "Выберите цель устойчивого развития:",
        reply_markup=builder.as_markup()
    )

# Обработчик выбора конкретной ЦУР
@router.callback_query(F.data.startswith("sdg_"))
async def show_sdg_detail(callback: CallbackQuery):
    sdg_num = int(callback.data.split("_")[1])
    title = SDG_TITLES.get(sdg_num)
    
    await callback.message.edit_text(
        f"🎯 **Цель {sdg_num}: {title}**\n\n"
        f"*Описание:* В разработке\n"
        f"*Для вашего возраста:* контент скоро появится",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Пройти квиз", callback_data=f"quiz_{sdg_num}")],
            [InlineKeyboardButton(text="🎥 Видео", callback_data=f"video_{sdg_num}")],
            [InlineKeyboardButton(text="📖 Подробнее", callback_data=f"more_{sdg_num}")],
            [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_sdg_list")]
        ])
    )
    await callback.answer()

# Назад к списку ЦУР
@router.callback_query(F.data == "back_to_sdg_list")
async def back_to_sdg_list_handler(callback: CallbackQuery):
    await show_sdg_list(callback)
    await callback.answer()

# Назад в главное меню
@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_kb()
    )
    await callback.answer()