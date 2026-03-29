from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from database import AsyncSessionLocal
from models import Question
from config import ADMIN_IDS
from sqlalchemy import select
from datetime import datetime

router = Router()

# Фильтр для проверки админа
def is_admin(message: Message) -> bool:
    return message.from_user.id in ADMIN_IDS

@router.message(Command("reply"), F.func(is_admin))
async def reply_to_question(message: Message, command: CommandObject, bot):
    if not command.args:
        await message.reply("❌ Формат: /reply <ID_вопроса> <текст ответа>")
        return
    
    try:
        # Парсим аргументы: /reply 15 текст ответа
        parts = command.args.split(' ', 1)
        question_id = int(parts[0])
        answer_text = parts[1] if len(parts) > 1 else ""
        
        if not answer_text:
            await message.reply("❌ Текст ответа не может быть пустым")
            return
        
    except ValueError:
        await message.reply("❌ Неверный формат ID вопроса")
        return
    
    # Находим вопрос в БД
    async with AsyncSessionLocal() as session:
        stmt = select(Question).where(Question.id == question_id)
        result = await session.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            await message.reply(f"❌ Вопрос #{question_id} не найден")
            return
        
        if question.status == 'answered':
            await message.reply(f"⚠️ На вопрос #{question_id} уже дан ответ")
            return
        
        # Отправляем ответ пользователю
        try:
            await bot.send_message(
                question.user_id,
                f"📩 **На вопрос {question.text} Эксперт (Имя эксперта) ответил: **\n\n"
                f"{answer_text}\n\n"
                f"Если остались вопросы, задайте новый.",
                parse_mode="Markdown"
            )
            
            # Обновляем статус в БД
            question.status = 'answered'
            question.answer = answer_text
            question.answered_at = datetime.utcnow()
            await session.commit()
            
            await message.reply(f"✅ Ответ отправлен пользователю {question.user_name}")
            
        except Exception as e:
            await message.reply(f"❌ Ошибка отправки: {str(e)}")

@router.message(Command("export_feedback"))
async def export_feedback(message: Message):
    # Проверка админа
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Недостаточно прав")
        return
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        stmt = select(Feedback).order_by(Feedback.created_at.desc())
        result = await session.execute(stmt)
        feedbacks = result.scalars().all()
    
    if not feedbacks:
        await message.answer("📭 Нет данных для выгрузки")
        return
    
    import csv
    import io
    from aiogram.types import BufferedInputFile
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "sdg_id", "usefulness", "interest", "clarity", "created_at"])
    
    for f in feedbacks:
        writer.writerow([f.id, f.user_id, f.sdg_id, f.usefulness, f.interest, f.clarity, f.created_at])
    
    # Отправка файла
    file = BufferedInputFile(output.getvalue().encode('utf-8'), filename="feedback.csv")
    await message.answer_document(file, caption="📊 Выгрузка обратной связи")
        writer.writerow([f.id, f.user_id, f.sdg_id, f.usefulness, f.interest, f.clarity, f.comment, f.created_at])
    
    await message.answer_document(
        BufferedInputFile(output.getvalue().encode('utf-8'), filename="feedback.csv"),
        caption="📊 Выгрузка обратной связи"
    )

# ---------- ВЫГРУЗКА ВОПРОСОВ ЭКСПЕРТУ ----------
@router.message(Command("export_questions"), F.func(is_admin))
async def export_questions(message: Message):
    async with AsyncSessionLocal() as session:
        stmt = select(Question).order_by(Question.created_at.desc())
        result = await session.execute(stmt)
        questions = result.scalars().all()
    
    if not questions:
        await message.answer("📭 Нет вопросов.")
        return
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "user_name", "text", "status", "answer", "created_at", "answered_at"])
    
    for q in questions:
        writer.writerow([q.id, q.user_id, q.user_name, q.text, q.status, q.answer, q.created_at, q.answered_at])
    
    await message.answer_document(
        BufferedInputFile(output.getvalue().encode('utf-8'), filename="questions.csv"),
        caption="❓ Выгрузка вопросов эксперту"
    )

# ---------- ВЫГРУЗКА ЗАЯВОК ПОСЛАННИКОВ ----------
@router.message(Command("export_ambassadors"), F.func(is_admin))
async def export_ambassadors(message: Message):
    async with AsyncSessionLocal() as session:
        stmt = select(AmbassadorApplication).order_by(AmbassadorApplication.created_at.desc())
        result = await session.execute(stmt)
        apps = result.scalars().all()
    
    if not apps:
        await message.answer("📭 Нет заявок.")
        return
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "full_name", "age", "institution", "city", "contact", "role", "status", "created_at", "reviewed_at"])
    
    for a in apps:
        writer.writerow([a.id, a.user_id, a.full_name, a.age, a.institution, a.city, a.contact, a.role, a.status, a.created_at, a.reviewed_at])
    
    await message.answer_document(
        BufferedInputFile(output.getvalue().encode('utf-8'), filename="ambassadors.csv"),
        caption="🎓 Выгрузка заявок посланников"
    )

# ---------- ОБЩАЯ СВОДКА ----------
@router.message(Command("stats_all"), F.func(is_admin))
async def stats_all(message: Message):
    async with AsyncSessionLocal() as session:
        total_users = await session.scalar(select(func.count()).select_from(User))
        total_games = await session.scalar(select(func.count()).select_from(GameResult))
        total_quizzes = await session.scalar(select(func.count()).select_from(QuizResult))
        total_feedback = await session.scalar(select(func.count()).select_from(Feedback))
        total_questions = await session.scalar(select(func.count()).select_from(Question))
        total_ambassadors = await session.scalar(select(func.count()).select_from(AmbassadorApplication))
        
        text = (
            f"📊 **Общая статистика бота**\n\n"
            f"👥 Пользователей: {total_users}\n"
            f"🎮 Прохождений игр: {total_games}\n"
            f"📚 Прохождений квизов: {total_quizzes}\n"
            f"💬 Отзывов: {total_feedback}\n"
            f"❓ Вопросов эксперту: {total_questions}\n"
            f"📝 Заявок посланников: {total_ambassadors}\n"
        )
        await message.answer(text, parse_mode="Markdown")
