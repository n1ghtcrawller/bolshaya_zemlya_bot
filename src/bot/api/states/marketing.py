from aiogram.fsm.state import State, StatesGroup


class MaterialUploadSG(StatesGroup):
    waiting_file = State()
    waiting_title = State()
    waiting_description = State()


class BroadcastCreateSG(StatesGroup):
    waiting_text = State()
    waiting_media = State()
    waiting_segment = State()
    waiting_confirm = State()


class ContentCreateSG(StatesGroup):
    waiting_title = State()
    waiting_body = State()
    waiting_region = State()
    waiting_scheduled = State()
    waiting_media = State()
    waiting_submit_choice = State()


class ExpoCreateSG(StatesGroup):
    waiting_title = State()
    waiting_location = State()
    waiting_starts = State()
    waiting_ends = State()
    waiting_products = State()
    waiting_description = State()


class ExpoAssistantSG(StatesGroup):
    waiting_question = State()


class CatalogCategoryCreateSG(StatesGroup):
    waiting_name = State()


class CatalogProductCreateSG(StatesGroup):
    waiting_name = State()
    waiting_short = State()
    waiting_full = State()
    waiting_price = State()
    waiting_specs = State()
    waiting_photo = State()
