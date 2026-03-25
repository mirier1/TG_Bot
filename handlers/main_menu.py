from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.main_menu_kb import get_main_kb
from keyboards.settings_kb import get_settings_kb

from handlers.sdg import show_sdg_list
from handlers.questions import ask_question_start
from handlers.ambassador import start_ambassador_form

router = Router()

@router.callback_query(F.data.startswith("menu_"))
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    menu_action = callback.data.replace("menu_", "")

    try:
        await callback.message.delete()
    except:
        pass
    
    menu_action = callback.data.replace("menu_", "")
    
    if menu_action == "sdg":
        await show_sdg_list(callback.message)
    elif menu_action == "games":
        from handlers.games.menu import get_games_menu_kb
        
        # УДАЛЯЕМ старое сообщение и отправляем НОВОЕ
        try:
            await callback.message.delete()
        except:
            pass
        
        # Отправляем новое сообщение с играми
        await callback.message.answer(
            "🎮 **Мини-игры**\n\nВыберите возрастную группу:",
            reply_markup=get_games_menu_kb(),
            parse_mode="Markdown"
        )
        return
    elif menu_action == "question":
        await ask_question_start(callback, state)
        return
    elif menu_action == "ambassador":
        await start_ambassador_form(callback, state)
        return
    elif menu_action == "contest":
        await callback.message.answer("🎥 Конкурс 'Я есть ЦУР' в разработке")
    elif menu_action == "settings":
        await callback.message.answer(
            "⚙️ **Настройки профиля**\n\n"
            "Выберите действие:",
            reply_markup=get_settings_kb(),  # ← Клавиатура настроек
            parse_mode="Markdown"
        )
    
    await callback.answer()