from aiogram.fsm.state import State, StatesGroup

class FeedbackStates(StatesGroup):
    usefulness = State()
    interest = State()
    clarity = State()
    comment = State()