from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from database import AsyncSessionLocal
from models import Question, User, GameResult, QuizResult, Feedback, AmbassadorApplication, UserActivity
from config import ADMIN_IDS
from sqlalchemy import select, func
from datetime import datetime, timedelta
from services.analytics import log_activity

router = Router()

def is_admin(message: Message) -> bool:
    return message.from_user.id in ADMIN_IDS

# ---------- ОТВЕТ НА ВОПРОС ----------
@router.message(Command("reply"), F.func(is_admin))
async def reply_to_question(message: Message, command: CommandObject, bot):
    if not command.args:
        await message.reply("❌ Формат: /reply <ID_вопроса> <текст ответа>")
        return
    
    try:
        parts = command.args.split(' ', 1)
        question_id = int(parts[0])
        answer_text = parts[1] if len(parts) > 1 else ""
        if not answer_text:
            await message.reply("❌ Текст ответа не может быть пустым")
            return
    except ValueError:
        await message.reply("❌ Неверный формат ID вопроса")
        return
    
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
        
        try:
            await bot.send_message(
                question.user_id,
                f"📩 **На ваш вопрос эксперт ответил:**\n\n{answer_text}\n\nЕсли остались вопросы, задайте новый.",
                parse_mode="Markdown"
            )
            question.status = 'answered'
            question.answer = answer_text
            question.answered_at = datetime.utcnow()
            await session.commit()
            await message.reply(f"✅ Ответ отправлен пользователю {question.user_name}")
        except Exception as e:
            await message.reply(f"❌ Ошибка отправки: {str(e)}")

# ---------- ВЫГРУЗКА FEEDBACK ----------
@router.message(Command("export_feedback"))
async def export_feedback(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Недостаточно прав")
        return
    
    async with AsyncSessionLocal() as session:
        stmt = select(Feedback).order_by(Feedback.created_at.desc())
        result = await session.execute(stmt)
        feedbacks = result.scalars().all()
    
    if not feedbacks:
        await message.answer("📭 Нет данных для выгрузки")
        return
    
    import csv, io
    from aiogram.types import BufferedInputFile
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["id", "user_id", "sdg_id", "usefulness", "interest", "clarity", "created_at"])
    for f in feedbacks:
        writer.writerow([f.id, f.user_id, f.sdg_id, f.usefulness, f.interest, f.clarity, f.created_at])
    
    file = BufferedInputFile(output.getvalue().encode('utf-8-sig'), filename="feedback.csv")
    await message.answer_document(file, caption="📊 Выгрузка обратной связи")

# ---------- ЗАЯВКИ ПОСЛАННИКОВ ----------
@router.message(Command("approve"), F.func(is_admin))
async def approve_ambassador(message: Message, command: CommandObject, bot):
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
            await message.reply(f"⚠️ Заявка #{application_id} уже обработана")
            return
        
        application.status = 'approved'
        application.reviewed_at = datetime.utcnow()
        await session.commit()
        
        try:
            await bot.send_message(
                application.user_id,
                f"🎉 **Поздравляем! Ваша заявка на статус посланника ЦУР одобрена!**\n\n"
                f"Роль: *{application.role}*\n\nМы свяжемся с вами для дальнейших инструкций. 🌍",
                parse_mode="Markdown"
            )
            await message.reply(f"✅ Заявка #{application_id} одобрена. Пользователь уведомлён.")
        except Exception as e:
            await message.reply(f"⚠️ Заявка одобрена, но не удалось уведомить: {str(e)}")

@router.message(Command("reject"), F.func(is_admin))
async def reject_ambassador(message: Message, command: CommandObject, bot):
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
        
        try:
            await bot.send_message(
                application.user_id,
                f"📩 **Ваша заявка на статус посланника ЦУР отклонена.**\nПричина: *{reason}*\n\nВы можете попробовать снова позже.",
                parse_mode="Markdown"
            )
            await message.reply(f"✅ Заявка #{application_id} отклонена.")
        except Exception as e:
            await message.reply(f"⚠️ Заявка отклонена, но не удалось уведомить: {str(e)}")

@router.message(Command("applications"), F.func(is_admin))
async def list_applications(message: Message):
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
        text += f"{status_emoji} **#{app.id}** | {app.full_name} | {app.role}\n   Статус: {app.status}\n\n"
    text += "Для одобрения: `/approve <ID>`\nДля отклонения: `/reject <ID> [причина]`"
    await message.answer(text, parse_mode="Markdown")

# ---------- СТАТИСТИКА АКТИВНОСТИ (РУСИФИЦИРОВАННАЯ) ----------
@router.message(Command("stats_activity"), F.func(is_admin))
async def stats_activity(message: Message):
    async with AsyncSessionLocal() as session:
        today = datetime.utcnow().date()
        stmt = select(func.count()).where(func.date(UserActivity.created_at) == today)
        today_activity = await session.scalar(stmt) or 0
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        stmt = select(UserActivity.action, func.count()).where(
            UserActivity.created_at >= week_ago
        ).group_by(UserActivity.action)
        result = await session.execute(stmt)
        actions = result.all()
        
        translate = {
            'game': '🎮 Игры',
            'viewsdg': '📚 Просмотры ЦУР',
            'view_sdg': '📚 Просмотры ЦУР',
            'quiz': '📝 Квизы',
            'gamesorting': '♻️ Сортировка мусора (старый лог)',
            'game_habits': '👍 Правильные привычки',
            'game_right_wrong': '❓ Что правильно?',
            'game_story': '📖 Сюжетная игра',
        }
        
        text = f"📊 **Активность за сегодня:** {today_activity}\n\n**За неделю:**\n"
        if actions:
            for action, count in actions:
                ru_action = translate.get(action, action)
                text += f"• {ru_action}: {count}\n"
        else:
            text += "Нет данных\n"
        
        await message.answer(text, parse_mode="Markdown")

# ---------- ПОПУЛЯРНОСТЬ ИГР ----------
@router.message(Command("stats_games_popular"), F.func(is_admin))
async def stats_games_popular(message: Message):
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
            await message.answer("📭 Нет данных об играх. Возможно, ещё никто не играл после последнего обновления.")
            return
        
        game_names = {
            # Новые записи (с подчёркиванием)
            'waste_young': '♻️ Сортировка мусора (5-7 кл)',
            'waste_teen': '♻️ Сортировка мусора (9-11 кл)',
            'habits_young': '👍 Правильные привычки (5-7 кл)',
            'habits_teen': '👍 Правильные привычки (9-11 кл)',
            'rightwrong_young': '❓ Что правильно? (5-7 кл)',
            'rightwrong_teen': '❓ Что правильно? (9-11 кл)',
            'story': '📖 Сюжетная игра',
            # Старые записи (без подчёркивания) для обратной совместимости
            'wasteyoung': '♻️ Сортировка мусора (5-7 кл)',
            'wasteteen': '♻️ Сортировка мусора (9-11 кл)',
            'habitsyoung': '👍 Правильные привычки (5-7 кл)',
            'habitsteen': '👍 Правильные привычки (9-11 кл)',
            'rightwrongyoung': '❓ Что правильно? (5-7 кл)',
            'rightwrongteen': '❓ Что правильно? (9-11 кл)',
        }
        
        text = "🎮 **Популярность игр:**\n\n"
        for details, count in rows:
            name = game_names.get(details, details)
            # Склонение
            if count == 1:
                ending = "запуск"
            elif 2 <= count <= 4:
                ending = "запуска"
            else:
                ending = "запусков"
            text += f"• {name}: {count} {ending}\n"
        
        await message.answer(text, parse_mode="Markdown")

# ---------- ПОПУЛЯРНЫЕ ЦУР ----------
@router.message(Command("stats_popular"), F.func(is_admin))
async def stats_popular(message: Message):
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