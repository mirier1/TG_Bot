from aiogram.fsm.state import State, StatesGroup

class QuizStates(StatesGroup):
    waiting_answer = State()   # Ждём ответ на вопрос
    waiting_next = State()     # Ждём нажатия "Далее"