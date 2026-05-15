from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.api.texts import REQUEST_CANCELLED

common_router = Router(name="common")


@common_router.message(Command("cancel"))
@common_router.message(F.text.casefold() == "✖️ отмена")
async def cancel_any(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer("Нет активной операции.", reply_markup=ReplyKeyboardRemove())
        return
    await message.answer(REQUEST_CANCELLED, reply_markup=ReplyKeyboardRemove())
