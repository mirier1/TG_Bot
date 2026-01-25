from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.sdg_keyboards import get_sdg_list_kb, get_sdg_detail_kb
from keyboards.main_menu_kb import get_main_kb
from utils.constants import SDG_TITLES

router = Router()

@router.message(F.text == "📚 Цели устойчивого развития")
@router.callback_query(F.data == "menu_sdg")
async def show_sdg_list(update: Message | CallbackQuery):
    if isinstance(update, CallbackQuery):
        message = update.message
        await update.answer()
        await message.delete()
    else:
        message = update
    
    await message.answer(
        "Выберите цель устойчивого развития:",
        reply_markup=get_sdg_list_kb()
    )

@router.callback_query(F.data.startswith("sdg_"))
async def show_sdg_detail(callback: CallbackQuery):
    sdg_num = int(callback.data.split("_")[1])
    title = SDG_TITLES.get(sdg_num)
    
    await callback.message.edit_text(
        f"🎯 **Цель {sdg_num}: {title}**\n\n"
        f"*Описание:* В разработке\n"
        f"*Для вашего возраста:* контент скоро появится",
        parse_mode="Markdown",
        reply_markup=get_sdg_detail_kb(sdg_num)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_sdg_list")
async def back_to_sdg_list_handler(callback: CallbackQuery):
    await show_sdg_list(callback)
    await callback.answer()

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