from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.api.keyboards.client import client_main_menu
from bot.api.keyboards.dealer import dealer_main_menu
from bot.api.keyboards.marketing import marketing_main_menu
from bot.api.keyboards.sales import head_of_sales_main_menu, sales_main_menu
from bot.api.texts import (
    ADMIN_MENU_HEADER,
    CLIENT_MENU_HEADER,
    DEALER_MENU_HEADER,
    GREETING_NEW,
    GREETING_RETURNING,
    HOS_MENU_HEADER,
    MKT_MENU_HEADER,
    SALES_MENU_HEADER,
)
from bot.core.enums import UserRole
from bot.db.models.user import User

start_router = Router(name="start")


@start_router.message(CommandStart())
async def handle_start(message: Message, app_user: User, state: FSMContext) -> None:
    await state.clear()
    text_template = GREETING_NEW if _is_first_seen(app_user) else GREETING_RETURNING
    await message.answer(text_template.format(name=app_user.full_name))
    await _send_role_menu(message, app_user.role)


async def _send_role_menu(message: Message, role: UserRole) -> None:
    if role is UserRole.CLIENT:
        await message.answer(CLIENT_MENU_HEADER, reply_markup=client_main_menu())
        return
    if role is UserRole.DEALER:
        await message.answer(DEALER_MENU_HEADER, reply_markup=dealer_main_menu())
        return
    if role is UserRole.SALES:
        await message.answer(SALES_MENU_HEADER, reply_markup=sales_main_menu())
        return
    if role is UserRole.HEAD_OF_SALES:
        await message.answer(HOS_MENU_HEADER, reply_markup=head_of_sales_main_menu())
        return
    if role is UserRole.MARKETING:
        await message.answer(MKT_MENU_HEADER, reply_markup=marketing_main_menu())
        return
    if role is UserRole.HEAD_OF_MARKETING:
        await message.answer(MKT_MENU_HEADER, reply_markup=marketing_main_menu())
        return
    if role is UserRole.ADMIN:
        await message.answer(ADMIN_MENU_HEADER, reply_markup=marketing_main_menu())
        return


def _is_first_seen(user: User) -> bool:
    """Если запись создана только что — created_at ≈ updated_at."""
    return (user.updated_at - user.created_at).total_seconds() < 2
