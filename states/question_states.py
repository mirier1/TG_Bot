from aiogram.fsm.state import State, StatesGroup

class QuestionForm(StatesGroup):
    text = State()  # Ожидаем текст вопроса