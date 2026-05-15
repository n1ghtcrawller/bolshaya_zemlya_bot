from aiogram.fsm.state import State, StatesGroup


class DealerProfileEditSG(StatesGroup):
    waiting_value = State()


class DealerMaterialSubmitSG(StatesGroup):
    waiting_file = State()
    waiting_title = State()
    waiting_description = State()
