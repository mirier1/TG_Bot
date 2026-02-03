from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from database import AsyncSessionLocal
from models import QuizResult, User
from data.quiz_questions import QUIZ_QUESTIONS
from handlers.states.quiz_states import QuizStates
from sqlalchemy import select
import random

router = Router()

async def get_user_age_group(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.age_group).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar()

async def get_user_quiz_result(user_id: int, sdg_id: int, difficulty: str, age_group: str):
    async with AsyncSessionLocal() as session:
        stmt = select(QuizResult).where(
            (QuizResult.user_id == user_id) &
            (QuizResult.sdg_id == sdg_id) &
            (QuizResult.difficulty == difficulty) &
            (QuizResult.age_group == age_group)
        ).order_by(QuizResult.created_at.desc())
        result = await session.execute(stmt)
        row = result.first()
        return row[0] if row else None

async def save_quiz_result(user_id: int, sdg_id: int, difficulty: str, 
                          age_group: str, score: int, total: int):
    async with AsyncSessionLocal() as session:
        stmt = select(QuizResult).where(
            (QuizResult.user_id == user_id) &
            (QuizResult.sdg_id == sdg_id) &
            (QuizResult.difficulty == difficulty) &
            (QuizResult.age_group == age_group)
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
                difficulty=difficulty,
                age_group=age_group,
                score=score,
                total=total
            )
            session.add(new_result)
        await session.commit()

async def show_difficulty_selection(callback: CallbackQuery, sdg_id: int, age_group: str):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🟢 Легкий", callback_data=f"diff_easy_{sdg_id}"),
        InlineKeyboardButton(text="🟡 Средний", callback_data=f"diff_medium_{sdg_id}"),
        InlineKeyboardButton(text="🔴 Сложный", callback_data=f"diff_hard_{sdg_id}"),
    )
    builder.adjust(1)
    
    await callback.message.edit_text(
        "Выберите уровень сложности:",
        reply_markup=builder.as_markup()
    )

async def start_new_quiz(callback: CallbackQuery, state: FSMContext, sdg_id: int, 
                        difficulty: str, age_group: str):
    try:
        questions = QUIZ_QUESTIONS[sdg_id][age_group][difficulty]
    except KeyError:
        await callback.answer("❌ Вопросы не найдены")
        return
    
    if not questions:
        await callback.answer("❌ Вопросы отсутствуют")
        return
    
    selected_questions = random.sample(questions, min(10, len(questions)))
    
    await state.update_data(
        sdg_id=sdg_id,
        difficulty=difficulty,
        age_group=age_group,
        questions=selected_questions,
        current_question=0,
        score=0
    )
    
    await show_question(callback, state)

@router.callback_query(F.data.startswith("quiz_"))
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    sdg_id = int(callback.data.split("_")[1])
    user_age_group = await get_user_age_group(callback.from_user.id)
    
    if not user_age_group:
        await callback.answer("❌ Укажите возраст в профиле", show_alert=True)
        return
    
    await show_difficulty_selection(callback, sdg_id, user_age_group)
    await callback.answer()

@router.callback_query(F.data.startswith("diff_"))
async def handle_difficulty_selection(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    difficulty = parts[1]
    sdg_id = int(parts[2])
    
    user_age_group = await get_user_age_group(callback.from_user.id)
    if not user_age_group:
        await callback.answer("❌ Ошибка: возраст не указан")
        return
    
    previous_result = await get_user_quiz_result(
        callback.from_user.id, 
        sdg_id, 
        difficulty,
        user_age_group
    )
    
    if previous_result:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="🔄 Попробовать еще раз",
                callback_data=f"restart_{difficulty}_{sdg_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="◀️ Выбрать другую сложность",
                callback_data=f"quiz_{sdg_id}"
            )
        )
        
        await callback.message.edit_text(
            f"📊 Ваш предыдущий результат (сложность: {difficulty}):\n"
            f"Счёт: {previous_result.score}/{previous_result.total}\n\n"
            f"Хотите попробовать еще раз?",
            reply_markup=builder.as_markup()
        )
    else:
        await start_new_quiz(callback, state, sdg_id, difficulty, user_age_group)
    
    await callback.answer()

@router.callback_query(F.data.startswith("restart_"))
async def restart_quiz(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    difficulty = parts[1]
    sdg_id = int(parts[2])
    
    user_age_group = await get_user_age_group(callback.from_user.id)
    if not user_age_group:
        await callback.answer("❌ Ошибка: возраст не указан")
        return
    
    await start_new_quiz(callback, state, sdg_id, difficulty, user_age_group)
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
    
    if is_correct:
        data["score"] += 1
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="➡️ Далее",
        callback_data="next_question"
    ))
    
    correct_answer_text = question["options"][question["correct"]]
    await callback.message.edit_text(
        f"{'✅ Верно!' if is_correct else f'❌ Неверно. Правильно: {correct_answer_text}'}\n\n"
        f"💡 {question['explanation']}",
        reply_markup=builder.as_markup()
    )
    
    await state.update_data(**data)
    await state.set_state(QuizStates.waiting_next)
    await callback.answer()

@router.callback_query(F.data == "next_question")
async def next_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["current_question"] += 1
    await state.update_data(**data)
    
    if data["current_question"] < len(data["questions"]):
        await show_question(callback, state)
    else:
        await finish_quiz(callback, state)
    await callback.answer()

async def finish_quiz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    score = data["score"]
    total = len(data["questions"])
    difficulty = data["difficulty"]
    sdg_id = data["sdg_id"]
    age_group = data["age_group"]
    
    await save_quiz_result(
        user_id=callback.from_user.id,
        sdg_id=sdg_id,
        difficulty=difficulty,
        age_group=age_group,
        score=score,
        total=total
    )
    
    percentage = (score / total) * 100
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔄 Попробовать еще раз",
            callback_data=f"restart_{difficulty}_{sdg_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📚 Выбрать другую сложность",
            callback_data=f"quiz_{sdg_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Вернуться к ЦУР",
            callback_data=f"sdg_{sdg_id}"
        )
    )
    
    await callback.message.edit_text(
        f"📊 **Результат квиза** (сложность: {difficulty})\n\n"
        f"Правильных ответов: {score}/{total}\n"
        f"Процент: {percentage:.0f}%\n\n"
        f"Результат сохранён.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.clear()