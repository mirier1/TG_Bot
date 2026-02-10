from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import AsyncSessionLocal
from models import GameResult
from sqlalchemy import select

async def save_game_result(user_id: int, game_type: str, age_group: str, 
                          score: int, max_score: int, steps: int):
    """Сохраняет или обновляет результат игры в БД"""
    async with AsyncSessionLocal() as session:
        stmt = select(GameResult).where(
            (GameResult.user_id == user_id) &
            (GameResult.game_type == game_type) &
            (GameResult.age_group == age_group)
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Обновляем если новый счет лучше
            if score > existing.score:
                existing.score = score
                existing.max_score = max_score
                existing.steps_completed = steps
        else:
            # Создаём новый результат
            new_result = GameResult(
                user_id=user_id,
                game_type=game_type,
                age_group=age_group,
                score=score,
                max_score=max_score,
                steps_completed=steps
            )
            session.add(new_result)
        
        await session.commit()

def create_game_keyboard(age_group: str, game_type: str):
    """Создаёт стандартную клавиатуру для игр"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Играть снова",
            callback_data=f"game_{game_type}_{age_group}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎮 Другие игры",
            callback_data=f"games_{age_group}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏠 В главное меню",
            callback_data="back_main_menu"
        )
    )
    
    return builder.as_markup()

def get_performance_text(score: int, max_score: int) -> str:
    """Возвращает текст оценки результатов"""
    percentage = (score / max_score) * 100
    
    if percentage >= 90:
        return "🏆 Отлично! Ты настоящий эксперт!"
    elif percentage >= 70:
        return "👍 Хорошо! Ты много знаешь!"
    elif percentage >= 50:
        return "👌 Неплохо! Есть куда стремиться!"
    else:
        return "💪 Продолжай учиться! Ты станешь лучше!"