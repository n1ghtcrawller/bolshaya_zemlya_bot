from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Contact, Message, ReplyKeyboardRemove
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import (
    ClientMenuCallback,
    back_to_menu,
    cancel_kb,
    confirm_request_kb,
    share_contact_kb,
)
from bot.api.states.client import CreateRequestSG
from bot.api.texts import (
    REQUEST_ASK_COMMENT,
    REQUEST_ASK_NAME,
    REQUEST_ASK_PHONE,
    REQUEST_CANCELLED,
    REQUEST_CONFIRM,
    REQUEST_CREATED,
    REQUEST_VALIDATION_FAILED,
)
from bot.db.models.user import User
from bot.schemas.request import ClientRequestCreate
from bot.services.request_service import RequestService

create_request_router = Router(name="client.create_request")


@create_request_router.callback_query(F.data == ClientMenuCallback.NEW_REQUEST)
async def start_create_request(
    call: CallbackQuery, app_user: User, state: FSMContext
) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.set_state(CreateRequestSG.name)
    await state.update_data(prefill_name=app_user.full_name)
    await call.message.answer(REQUEST_ASK_NAME, reply_markup=cancel_kb())


@create_request_router.message(CreateRequestSG.name, F.text)
async def receive_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await state.update_data(contact_name=name)
    await state.set_state(CreateRequestSG.phone)
    await message.answer(REQUEST_ASK_PHONE, reply_markup=share_contact_kb())


@create_request_router.message(CreateRequestSG.phone, F.contact)
async def receive_contact(message: Message, state: FSMContext) -> None:
    contact: Contact | None = message.contact
    if contact is None or not contact.phone_number:
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await state.update_data(contact_phone=contact.phone_number)
    await state.set_state(CreateRequestSG.comment)
    await message.answer(REQUEST_ASK_COMMENT, reply_markup=ReplyKeyboardRemove())


@create_request_router.message(CreateRequestSG.phone, F.text)
async def receive_phone_text(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not any(ch.isdigit() for ch in raw):
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await state.update_data(contact_phone=raw)
    await state.set_state(CreateRequestSG.comment)
    await message.answer(REQUEST_ASK_COMMENT, reply_markup=ReplyKeyboardRemove())


@create_request_router.message(CreateRequestSG.comment, F.text)
async def receive_comment(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    user_comment = None if raw in {"", "-"} else raw
    data = await state.get_data()
    prefix = data.get("comment_prefix")
    if prefix and user_comment:
        comment: str | None = f"{prefix}\n\n{user_comment}"
    else:
        comment = prefix or user_comment
    data = await state.update_data(comment=comment)
    await state.set_state(CreateRequestSG.confirm)
    await message.answer(
        REQUEST_CONFIRM.format(
            contact_name=data["contact_name"],
            contact_phone=data["contact_phone"],
            comment=comment or "—",
        ),
        reply_markup=confirm_request_kb(),
    )


@create_request_router.callback_query(
    CreateRequestSG.confirm, F.data == "client:req:confirm"
)
async def confirm_request(
    call: CallbackQuery, app_user: User, session: AsyncSession, state: FSMContext
) -> None:
    await call.answer()
    if call.message is None:
        return
    data = await state.get_data()
    try:
        payload = ClientRequestCreate(
            contact_name=data["contact_name"],
            contact_phone=data["contact_phone"],
            comment=data.get("comment"),
        )
    except ValidationError:
        await call.message.answer(REQUEST_VALIDATION_FAILED, reply_markup=back_to_menu())
        await state.clear()
        return

    service = RequestService(session)
    request = await service.create_for_user(app_user.id, payload)
    await state.clear()
    await call.message.answer(
        REQUEST_CREATED.format(id=request.id), reply_markup=back_to_menu()
    )


@create_request_router.callback_query(
    CreateRequestSG.confirm, F.data == "client:req:cancel"
)
async def cancel_request(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await state.clear()
    if call.message is not None:
        await call.message.answer(REQUEST_CANCELLED, reply_markup=back_to_menu())
