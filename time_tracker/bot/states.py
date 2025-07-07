from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_category = State()
    waiting_for_activity_name = State()
    waiting_for_duration = State() 