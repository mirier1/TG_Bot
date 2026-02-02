from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import AsyncSessionLocal
from models import QuizResult
from data.quiz_questions import QUIZ_QUESTIONS
from handlers.states.quiz_states import QuizStates
import asyncio

router = Router()

class QuizStates(StatesGroup):
    waiting_answer = State()

@router.callback_query(F.data.startswith("quiz_"))
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    sdg_id = int(callback.data.split("_")[1])
    
    # Берём вопросы для этой ЦУР
    quiz_questions = QUIZ_QUESTIONS.get(sdg_id, [])
    
    if not quiz_questions:
        await callback.answer("Квиз для этой ЦУР пока не готов 😔")
        return
    
    # Сохраняем в состояние
    await state.update_data(
        sdg_id=sdg_id,
        questions=quiz_questions,
        current_question=0,
        score=0,
        user_answers=[]
    )
    
    # Показываем первый вопрос
    await show_question(callback, state)
    await callback.answer()

async def show_question(callback: CallbackQuery, state: FSMContext):
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
    user_answer = int(callback.data.split("_")[1])
    data = await state.get_data()
    
    question = data["questions"][data["current_question"]]
    is_correct = user_answer == question["correct"]
    
    # Обновляем счёт
    if is_correct:
        data["score"] += 1
        feedback = "✅ Верно!"
    else:
        feedback = f"❌ Неверно. Правильно: {question['options'][question['correct']]}"
    
    data["user_answers"].append(user_answer)
    
    # Показываем ответ с кнопкой "Далее"
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
    await state.set_state(QuizStates.waiting_next)  # Новое состояние
    await callback.answer()

# НОВЫЙ обработчик для кнопки "Далее"
@router.callback_query(F.data == "next_question")
async def next_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["current_question"] += 1
    
    await state.update_data(**data)
    
    # Следующий вопрос или завершение
    if data["current_question"] < len(data["questions"]):
        await show_question(callback, state)
    else:
        await finish_quiz(callback, state)
    
    await callback.answer()

async def finish_quiz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    score = data["score"]
    total = len(data["questions"])
    
    # Сохраняем в БД
    async with AsyncSessionLocal() as session:
        result = QuizResult(
            user_id=callback.from_user.id,
            sdg_id=data["sdg_id"],
            score=score,
            total=total
        )
        session.add(result)
        await session.commit()
    
    # Показываем результат
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