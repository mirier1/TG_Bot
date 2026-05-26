from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from keyboards.main_menu_kb import get_main_kb
from utils.constants import SDG_TITLES
from keyboards.sdg_keyboards import SHORT_SDG_TITLES, get_sdg_list_kb, get_sdg_detail_kb, get_sdg_back_kb
from services.analytics import log_activity

router = Router()


# Обработчик текстового сообщения от reply-кнопок ЦУР
@router.message(F.text.in_(SHORT_SDG_TITLES.values()))
async def handle_sdg_reply_button(message: Message):
    # Находим номер ЦУР по тексту кнопки
    sdg_num = None
    for num, title in SHORT_SDG_TITLES.items():
        if title == message.text:
            sdg_num = num
            break

    if sdg_num is None:
        await message.answer("❌ Не удалось определить цель.")
        return

    await log_activity(
        user_id=message.from_user.id,
        action="view_sdg",
        target_id=sdg_num,
        details=f"sdg_{sdg_num}"
    )

    title = SDG_TITLES.get(sdg_num)
    await message.answer(
        f"🎯 **Цель {sdg_num}: {title}**\n\n"
        f"Текст ЦУР для данной возрастной группы",
        reply_markup=get_sdg_detail_kb(sdg_num),
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(F.text == "📚 Цели устойчивого развития")
@router.callback_query(F.data == "menu_sdg")
async def show_sdg_list(update: Message | CallbackQuery):
    if isinstance(update, CallbackQuery):
        message = update.message
        await update.answer()
        try:
            await message.delete()
        except:
            pass
    else:
        message = update

    await message.answer(
        "🌍 <b>Цели устойчивого развития</b>\n\n"
        "Выберите цель, чтобы узнать подробнее:",
        reply_markup=get_sdg_list_kb(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "back_to_sdg_list")
async def back_to_sdg_list_handler(callback: CallbackQuery):
    # Убираем старую inline-клавиатуру и показываем reply-список заново
    await callback.message.delete()
    await callback.message.answer(
        "🌍 <b>Цели устойчивого развития</b>\n\n"
        "Выберите цель, чтобы узнать подробнее:",
        reply_markup=get_sdg_list_kb(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass

    # При возврате в главное меню убираем reply-клавиатуру
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_sdg_"))
async def back_to_lecture(callback: CallbackQuery):
    sdg_num = int(callback.data.split("_")[3])
    title = SDG_TITLES.get(sdg_num)
    await callback.message.edit_text(
        f"🎯 **Цель {sdg_num}: {title}**\n\n"
        f"Текст для данной возрастной группы",
        reply_markup=get_sdg_detail_kb(sdg_num)
    )
    await callback.answer()