from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.main_menu_kb import get_main_kb

router = Router()

@router.callback_query(F.data == "back_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_kb()
    )
    await callback.answer()