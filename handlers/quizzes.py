from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from database import AsyncSessionLocal
from models import QuizResult
from data.quiz_questions import QUIZ_QUESTIONS
from handlers.states.quiz_states import QuizStates
from sqlalchemy import select
import asyncio

router = Router()

async def get_user_quiz_progress(user_id: int, sdg_id: int):
    """Возвращает последний результат квиза"""
    async with AsyncSessionLocal() as session:
        stmt = select(QuizResult).where(
            (QuizResult.user_id == user_id) &
            (QuizResult.sdg_id == sdg_id)
        ).order_by(QuizResult.created_at.desc())
        
        result = await session.execute(stmt)
        row = result.first()
        return row[0] if row else None

async def save_or_update_result(user_id: int, sdg_id: int, score: int, total: int):
    """Сохраняет или обновляет результат"""
    async with AsyncSessionLocal() as session:
        stmt = select(QuizResult).where(
            (QuizResult.user_id == user_id) &
            (QuizResult.sdg_id == sdg_id)
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.score = score
            existing.total = total
        else:
            new_result = QuizResult(
                user_id=user_id,
                sdg_id=sdg_id,
                score=score,
                total=total
            )
            session.add(new_result)
        
        await session.commit()

async def start_new_quiz(callback: CallbackQuery, state: FSMContext, sdg_id: int):
    """Запускает новый квиз"""
    quiz_questions = QUIZ_QUESTIONS.get(sdg_id, [])
    
    if not quiz_questions:
        await callback.answer("Квиз для этой ЦУР пока не готов 😔")
        return
    
    await state.update_data(
        sdg_id=sdg_id,
        questions=quiz_questions,
        current_question=0,
        score=0
    )
    
    await show_question(callback, state)

@router.callback_query(F.data.startswith("quiz_"))
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Пройти квиз'"""
    sdg_id = int(callback.data.split("_")[1])
    previous_result = await get_user_quiz_progress(callback.from_user.id, sdg_id)
    
    if previous_result:
        # Показываем результат и предлагаем перепройти
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="🔄 Пройти заново",
                callback_data=f"restart_quiz_{sdg_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"sdg_{sdg_id}"
            )
        )
        
        await callback.message.edit_text(
            f"📊 Вы уже проходили этот квиз:\n"
            f"Результат: {previous_result.score}/{previous_result.total}\n"
            f"Процент: {(previous_result.score/previous_result.total)*100:.0f}%\n"
            f"Дата: {previous_result.created_at.strftime('%d.%m.%Y')}\n\n"
            f"Хотите пройти заново?",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    
    await start_new_quiz(callback, state, sdg_id)
    await callback.answer()

@router.callback_query(F.data.startswith("restart_quiz_"))
async def restart_quiz(callback: CallbackQuery, state: FSMContext):
    """Перезапуск квиза"""
    sdg_id = int(callback.data.split("_")[2])
    await start_new_quiz(callback, state, sdg_id)
    await callback.answer()

async def show_question(callback: CallbackQuery, state: FSMContext):
    """Показывает текущий вопрос"""
    data = await state.get_data()
    question_index = data["current_question"]
    question = data["questions"][question_index]
    
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(question["options"]):
        builder.add(InlineKeyboardButton(
            text=option,
            callback_data=f"answer_{i}"
        ))
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"❓ Вопрос {question_index + 1}/{len(data['questions'])}:\n\n"
        f"{question['question']}",
        reply_markup=builder.as_markup()
    )
    
    await state.set_state(QuizStates.waiting_answer)

@router.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа пользователя"""
    user_answer = int(callback.data.split("_")[1])
    data = await state.get_data()
    
    question = data["questions"][data["current_question"]]
    is_correct = user_answer == question["correct"]
    
    if is_correct:
        data["score"] += 1
        feedback = "✅ Верно!"
    else:
        feedback = f"❌ Неверно. Правильно: {question['options'][question['correct']]}"
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="➡️ Далее",
        callback_data="next_question"
    ))
    
    await callback.message.edit_text(
        f"{feedback}\n\n💡 {question['explanation']}",
        reply_markup=builder.as_markup()
    )
    
    await state.update_data(**data)
    await state.set_state(QuizStates.waiting_next)
    await callback.answer()

@router.callback_query(F.data == "next_question")
async def next_question(callback: CallbackQuery, state: FSMContext):
    """Переход к следующему вопросу"""
    data = await state.get_data()
    data["current_question"] += 1
    
    await state.update_data(**data)
    
    if data["current_question"] < len(data["questions"]):
        await show_question(callback, state)
    else:
        await finish_quiz(callback, state)
    
    await callback.answer()

async def finish_quiz(callback: CallbackQuery, state: FSMContext):
    """Завершение квиза"""
    data = await state.get_data()
    score = data["score"]
    total = len(data["questions"])
    
    await save_or_update_result(
        user_id=callback.from_user.id,
        sdg_id=data["sdg_id"],
        score=score,
        total=total
    )
    
    percentage = (score / total) * 100
    if percentage >= 80:
        grade = "Отлично! 🎉"
    elif percentage >= 60:
        grade = "Хорошо! 👍"
    else:
        grade = "Можно лучше! 📚"
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="◀️ Вернуться к ЦУР",
        callback_data=f"sdg_{data['sdg_id']}"
    ))
    
    await callback.message.edit_text(
        f"📊 **Результат квиза**\n\n"
        f"Правильных ответов: {score}/{total}\n"
        f"Процент: {percentage:.0f}%\n"
        f"Оценка: {grade}\n\n"
        f"Результат сохранён.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.clear()