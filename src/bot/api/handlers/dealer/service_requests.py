from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.api.keyboards.dealer import DealerMenuCallback, back_to_menu
from bot.api.texts import DEALER_SERVICE_REQUESTS_EMPTY

service_requests_router = Router(name="dealer.service_requests")


@service_requests_router.callback_query(F.data == DealerMenuCallback.SERVICE_REQUESTS)
async def show_service_requests(call: CallbackQuery) -> None:
    await call.answer()
    if call.message is None:
        return
    await call.message.answer(DEALER_SERVICE_REQUESTS_EMPTY, reply_markup=back_to_menu())
