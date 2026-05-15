from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.api.keyboards.client import client_main_menu
from bot.api.texts import CLIENT_MENU_HEADER

client_menu_router = Router(name="client.menu")


@client_menu_router.callback_query(F.data == "client:back_to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer()
    if call.message is None:
        return
    await call.message.answer(CLIENT_MENU_HEADER, reply_markup=client_main_menu())
