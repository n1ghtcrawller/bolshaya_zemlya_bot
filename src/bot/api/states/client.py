from aiogram.fsm.state import State, StatesGroup


class CreateRequestSG(StatesGroup):
    name = State()
    phone = State()
    comment = State()
    confirm = State()
