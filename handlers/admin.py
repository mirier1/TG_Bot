from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from database import AsyncSessionLocal
from models import Question, User, GameResult, QuizResult, Feedback, AmbassadorApplication
from config import ADMIN_IDS
from sqlalchemy import select
from datetime import datetime, timedelta

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
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["id", "user_id", "sdg_id", "usefulness", "interest", "clarity", "created_at"])
    
    for f in feedbacks:
        writer.writerow([f.id, f.user_id, f.sdg_id, f.usefulness, f.interest, f.clarity, f.created_at])
    
    # Отправка файла
    file = BufferedInputFile(output.getvalue().encode('utf-8-sig'), filename="feedback.csv")
    await message.answer_document(file, caption="📊 Выгрузка обратной связи")

#ПРИНЯТИЕ ЗАЯВКИ ПОСЛАННИКА
@router.message(Command("approve"), F.func(is_admin))
async def approve_ambassador(message: Message, command: CommandObject, bot):
    """Принятие заявки посланника. Формат: /approve <ID_заявки>"""
    if not command.args:
        await message.reply("❌ Формат: /approve <ID_заявки>")
        return
    
    try:
        application_id = int(command.args.strip())
    except ValueError:
        await message.reply("❌ Неверный формат ID заявки")
        return
    
    async with AsyncSessionLocal() as session:
        stmt = select(AmbassadorApplication).where(AmbassadorApplication.id == application_id)
        result = await session.execute(stmt)
        application = result.scalar_one_or_none()
        
        if not application:
            await message.reply(f"❌ Заявка #{application_id} не найдена")
            return
        
        if application.status != 'pending':
            await message.reply(f"⚠️ Заявка #{application_id} уже обработана (статус: {application.status})")
            return
        
        # Обновляем статус
        application.status = 'approved'
        application.reviewed_at = datetime.utcnow()
        await session.commit()
        
        # Отправляем уведомление пользователю
        try:
            await bot.send_message(
                application.user_id,
                f"🎉 **Поздравляем! Ваша заявка на статус посланника ЦУР одобрена!**\n\n"
                f"Вы выбрали роль: *{application.role}*\n\n"
                f"Мы свяжемся с вами для дальнейших инструкций.\n"
                f"Спасибо за ваше желание изменить мир к лучшему! 🌍",
                parse_mode="Markdown"
            )
            await message.reply(f"✅ Заявка #{application_id} одобрена. Пользователь уведомлён.")
        except Exception as e:
            await message.reply(f"⚠️ Заявка одобрена, но не удалось уведомить пользователя: {str(e)}")

#ОТКЛОНЕНИЕ ЗАЯВКИ ПОСЛАННИКА
@router.message(Command("reject"), F.func(is_admin))
async def reject_ambassador(message: Message, command: CommandObject, bot):
    """Отклонение заявки посланника. Формат: /reject <ID_заявки> [причина]"""
    if not command.args:
        await message.reply("❌ Формат: /reject <ID_заявки> [причина]")
        return
    
    parts = command.args.split(' ', 1)
    try:
        application_id = int(parts[0])
        reason = parts[1] if len(parts) > 1 else "Не указана"
    except ValueError:
        await message.reply("❌ Неверный формат ID заявки")
        return
    
    async with AsyncSessionLocal() as session:
        stmt = select(AmbassadorApplication).where(AmbassadorApplication.id == application_id)
        result = await session.execute(stmt)
        application = result.scalar_one_or_none()
        
        if not application:
            await message.reply(f"❌ Заявка #{application_id} не найдена")
            return
        
        if application.status != 'pending':
            await message.reply(f"⚠️ Заявка #{application_id} уже обработана")
            return
        
        application.status = 'rejected'
        application.reviewed_at = datetime.utcnow()
        await session.commit()
        
        # Отправляем уведомление пользователю
        try:
            await bot.send_message(
                application.user_id,
                f"📩 **Ваша заявка на статус посланника ЦУР**\n\n"
                f"К сожалению, ваша заявка была отклонена.\n"
                f"Причина: *{reason}*\n\n"
                f"Вы можете попробовать подать заявку снова позже.",
                parse_mode="Markdown"
            )
            await message.reply(f"✅ Заявка #{application_id} отклонена. Пользователь уведомлён.")
        except Exception as e:
            await message.reply(f"⚠️ Заявка отклонена, но не удалось уведомить пользователя: {str(e)}")

# ---------- ПРОСМОТР ЗАЯВОК ----------
@router.message(Command("applications"), F.func(is_admin))
async def list_applications(message: Message):
    """Просмотр всех заявок посланников"""
    async with AsyncSessionLocal() as session:
        stmt = select(AmbassadorApplication).order_by(AmbassadorApplication.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        apps = result.scalars().all()
    
    if not apps:
        await message.answer("📭 Нет заявок.")
        return
    
    text = "📋 **Последние заявки посланников:**\n\n"
    for app in apps:
        status_emoji = "⏳" if app.status == "pending" else "✅" if app.status == "approved" else "❌"
        text += f"{status_emoji} **#{app.id}** | {app.full_name} | {app.role}\n"
        text += f"   Статус: {app.status}\n\n"
    
    text += "Для одобрения: `/approve <ID>`\nДля отклонения: `/reject <ID> [причина]`"
    
    await message.answer(text, parse_mode="Markdown")


# ---------- СТАТИСТИКА АКТИВНОСТИ ----------
@router.message(Command("stats_activity"), F.func(is_admin))
async def stats_activity(message: Message):
    """Активность пользователей за сегодня/неделю"""
    from datetime import datetime, timedelta
    
    async with AsyncSessionLocal() as session:
        # За сегодня
        today = datetime.utcnow().date()
        stmt = select(func.count()).where(func.date(UserActivity.created_at) == today)
        today_activity = await session.scalar(stmt) or 0
        
        # За неделю
        week_ago = datetime.utcnow() - timedelta(days=7)
        stmt = select(UserActivity.action, func.count()).where(
            UserActivity.created_at >= week_ago
        ).group_by(UserActivity.action)
        result = await session.execute(stmt)
        actions = result.all()
        
        text = f"📊 **Активность за сегодня:** {today_activity}\n\n"
        text += "**За неделю:**\n"
        if actions:
            for action, count in actions:
                text += f"• {action}: {count}\n"
        else:
            text += "Нет данных\n"
        
        await message.answer(text, parse_mode="Markdown")

# ---------- ПОПУЛЯРНЫЕ ЦУР ----------
@router.message(Command("stats_popular"), F.func(is_admin))
async def stats_popular(message: Message):
    """Топ-5 популярных ЦУР"""
    async with AsyncSessionLocal() as session:
        stmt = select(
            UserActivity.target_id, 
            func.count()
        ).where(
            UserActivity.action == 'view_sdg'
        ).group_by(
            UserActivity.target_id
        ).order_by(
            func.count().desc()
        ).limit(5)
        
        result = await session.execute(stmt)
        rows = result.all()
        
        if not rows:
            await message.answer("📭 Нет данных о просмотрах ЦУР")
            return
        
        text = "🏆 **Топ-5 популярных ЦУР:**\n\n"
        for target_id, count in rows:
            text += f"ЦУР {target_id}: {count} просмотров\n"
        
        await message.answer(text, parse_mode="Markdown")

# ---------- ПОПУЛЯРНОСТЬ ИГР ----------
@router.message(Command("stats_games_popular"), F.func(is_admin))
async def stats_games_popular(message: Message):
    """Популярность игр"""
    async with AsyncSessionLocal() as session:
        stmt = select(
            UserActivity.details, 
            func.count()
        ).where(
            UserActivity.action == 'game'
        ).group_by(
            UserActivity.details
        ).order_by(
            func.count().desc()
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        
        if not rows:
            await message.answer("📭 Нет данных об играх")
            return
        
        text = "🎮 **Популярность игр:**\n\n"
        for details, count in rows:
            text += f"• {details}: {count} запусков\n"
        
        await message.answer(text, parse_mode="Markdown")