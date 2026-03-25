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
    if not is_admin(message):
        return
    
    async with AsyncSessionLocal() as session:
        stmt = select(Feedback).order_by(Feedback.created_at.desc())
        result = await session.execute(stmt)
        feedbacks = result.scalars().all()
    
    # Генерация CSV
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "usefulness", "interest", "clarity", "comment", "created_at"])
    
    for f in feedbacks:
        writer.writerow([f.id, f.user_id, f.usefulness, f.interest, f.clarity, f.comment, f.created_at])
    
    # Отправка файла
    from aiogram.types import BufferedInputFile
    await message.answer_document(
        BufferedInputFile(output.getvalue().encode(), filename="feedback.csv"),
        caption="📊 Выгрузка обратной связи"
    )