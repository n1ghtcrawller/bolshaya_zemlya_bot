from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.api.keyboards.dealer import DealerMenuCallback, dealer_main_menu
from bot.api.texts import DEALER_MENU_HEADER

menu_router = Router(name="dealer.menu")


@menu_router.callback_query(F.data == DealerMenuCallback.BACK_TO_MENU)
async def back_to_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer()
    if call.message is None:
        return
    await call.message.answer(DEALER_MENU_HEADER, reply_markup=dealer_main_menu())


@menu_router.callback_query(F.data == "dealer:noop")
async def noop(call: CallbackQuery) -> None:
    await call.answer()
