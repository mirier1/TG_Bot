"""
Инициализация модуля игр.
Экспортирует все игровые роутеры.
"""
from aiogram import Router

from .menu import router as menu_router
from .waste_sorting import router as waste_router
from .good_habits import router as habits_router
from .right_wrong import router as right_wrong_router
from .common import router as common_router

# Создаём общий роутер для игр
games_router = Router()

# Включаем все роутеры игр
games_router.include_router(menu_router)
games_router.include_router(waste_router)
games_router.include_router(habits_router)
games_router.include_router(right_wrong_router)
games_router.include_router(common_router)

# Экспортируем для основного бота
__all__ = ['games_router']