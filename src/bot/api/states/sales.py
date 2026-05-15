from aiogram.fsm.state import State, StatesGroup


class SalesAssistantSG(StatesGroup):
    waiting_question = State()
