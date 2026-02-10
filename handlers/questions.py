from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from database import AsyncSessionLocal
from models import Question
from keyboards.main_menu_kb import get_main_kb
from handlers.states.question_states import QuestionForm
from config import ADMIN_CHAT_ID
from sqlalchemy import select

router = Router()

# Запуск режима вопроса
@router.callback_query(F.data == "menu_question")
async def ask_question_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QuestionForm.text)
    await callback.message.answer(
        "📝 **Задайте вопрос эксперту**\n\n"
        "Напишите ваш вопрос и мы отправим его специалисту.\n"
        "Ответ придёт в этом же чате.\n\n"
        "Для отмены используйте /cancel",
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

# Отмена вопроса
@router.message(Command("cancel"))
async def cancel_question(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Вопрос отменён.",
        reply_markup=get_main_kb()
    )

# Приём вопроса от пользователя
@router.message(QuestionForm.text)
async def process_question(message: Message, state: FSMContext, bot):
    if len(message.text) < 5:
        await message.answer("❌ Вопрос слишком короткий. Минимум 5 символов.\nПопробуйте еще раз.")
        return
    
    # Сохраняем в БД
    async with AsyncSessionLocal() as session:
        question = Question(
            user_id=message.from_user.id,
            user_name=message.from_user.username or message.from_user.first_name,
            message_id=message.message_id,
            text=message.text
        )
        session.add(question)
        await session.flush()  # Получаем ID вопроса
        
        # Отправляем в админ-чат
        admin_msg = await bot.send_message(
            ADMIN_CHAT_ID,
            f"❓ Вопрос #{question.id}\n"
            f"От: {question.user_name} (ID: {question.user_id})\n"
            f"Время: {question.created_at.strftime('%H:%M %d.%m.%Y')}\n"
            f"─────────────────\n"
            f"{question.text}\n\n"
            f"Ответить: /reply {question.id} [текст ответа]"
        )
        
        # Сохраняем ID сообщения в админ-чате
        question.admin_chat_message_id = admin_msg.message_id
        await session.commit()
    
    # Подтверждаем пользователю
    await message.answer(
        f"✅ Ваш вопрос отправлен эксперту!\n"
        f"Ответ придёт в этом чате.",
        reply_markup=get_main_kb()
    )
    
    await state.clear()