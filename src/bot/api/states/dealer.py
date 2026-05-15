from aiogram.fsm.state import State, StatesGroup


class DealerProfileEditSG(StatesGroup):
    waiting_value = State()
