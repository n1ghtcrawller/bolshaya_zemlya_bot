from aiogram.fsm.state import State, StatesGroup


class CreateRequestSG(StatesGroup):
    name = State()
    phone = State()
    comment = State()
    confirm = State()


class ChatWithManagerSG(StatesGroup):
    waiting_topic = State()
    waiting_phone = State()


class CallbackSG(StatesGroup):
    waiting_phone = State()
    waiting_note = State()


class ServiceRequestSG(StatesGroup):
    waiting_issue = State()
    waiting_equipment = State()
    waiting_description = State()
    waiting_phone = State()
