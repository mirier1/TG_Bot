from aiogram.fsm.state import State, StatesGroup

class AmbassadorForm(StatesGroup):
    name = State()
    age = State()
    institution = State()
    city = State()
    contact = State()
    role = State()
    confirm = State()