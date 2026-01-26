from aiogram import Router, F
from aiogram.types import CallbackQuery
from handlers.sdg import show_sdg_list
from keyboards.main_menu_kb import get_main_kb
from keyboards.settings_kb import get_settings_kb

router = Router()

@router.callback_query(F.data.startswith("menu_"))
async def handle_main_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    
    menu_action = callback.data.replace("menu_", "")
    
    if menu_action == "sdg":
        await show_sdg_list(callback.message)
    elif menu_action == "games":
        await callback.message.answer("🎮 Раздел мини-игр в разработке")
    elif menu_action == "question":
        await callback.message.answer("❓ Раздел вопросов эксперту в разработке")
    elif menu_action == "ambassador":
        await callback.message.answer("🎓 Форма 'Стать посланником' в разработке")
    elif menu_action == "contest":
        await callback.message.answer("🎥 Конкурс 'Я есть ЦУР' в разработке")
    elif menu_action == "feedback":
        await callback.message.answer("📊 Обратная связь в разработке")
    elif menu_action == "settings":
        await callback.message.answer(
            "⚙️ **Настройки профиля**\n\n"
            "Выберите действие:",
            reply_markup=get_settings_kb(),  # ← Клавиатура настроек
            parse_mode="Markdown"
        )
    
    await callback.answer()