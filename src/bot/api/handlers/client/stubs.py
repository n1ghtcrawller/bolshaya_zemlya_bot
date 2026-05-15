from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.api.keyboards.client import ClientMenuCallback, back_to_menu
from bot.api.texts import CLIENT_MENU_HINT

stubs_router = Router(name="client.stubs")

STUB_CALLBACKS = (ClientMenuCallback.FIND_DEALER,)


@stubs_router.callback_query(F.data.in_(set(STUB_CALLBACKS)))
async def stub_handler(call: CallbackQuery) -> None:
    await call.answer()
    if call.message is None:
        return
    await call.message.answer(CLIENT_MENU_HINT, reply_markup=back_to_menu())
