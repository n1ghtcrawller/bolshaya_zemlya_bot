from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.api.keyboards.marketing import MktMenuCallback, marketing_main_menu
from bot.api.texts import MKT_MENU_HEADER

menu_router = Router(name="marketing.menu")


@menu_router.callback_query(F.data == MktMenuCallback.BACK_TO_MENU)
async def back_to_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer()
    if call.message is None:
        return
    await call.message.answer(MKT_MENU_HEADER, reply_markup=marketing_main_menu())
