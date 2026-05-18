from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Contact, Message, ReplyKeyboardRemove
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import (
    ClientMenuCallback,
    back_to_menu,
    cancel_kb,
    share_contact_kb,
)
from bot.api.states.client import CallbackSG
from bot.api.texts import (
    CLIENT_CALLBACK_ASK_NOTE,
    CLIENT_CALLBACK_ASK_PHONE,
    CLIENT_CALLBACK_CREATED,
    CLIENT_CALLBACK_INTRO,
    REQUEST_VALIDATION_FAILED,
)
from bot.core.enums import LeadType
from bot.db.models.user import User
from bot.schemas.request import ClientRequestCreate
from bot.services.request_service import RequestService

callback_router = Router(name="client.callback")


@callback_router.callback_query(F.data == ClientMenuCallback.CALL)
async def start_callback(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.set_state(CallbackSG.waiting_phone)
    await call.message.answer(CLIENT_CALLBACK_INTRO)
    await call.message.answer(CLIENT_CALLBACK_ASK_PHONE, reply_markup=share_contact_kb())


@callback_router.message(CallbackSG.waiting_phone, F.contact)
async def phone_contact(message: Message, state: FSMContext) -> None:
    contact: Contact | None = message.contact
    if contact is None or not contact.phone_number:
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await state.update_data(phone=contact.phone_number)
    await state.set_state(CallbackSG.waiting_note)
    await message.answer(CLIENT_CALLBACK_ASK_NOTE, reply_markup=ReplyKeyboardRemove())


@callback_router.message(CallbackSG.waiting_phone, F.text)
async def phone_text(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not any(ch.isdigit() for ch in raw):
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await state.update_data(phone=raw)
    await state.set_state(CallbackSG.waiting_note)
    await message.answer(CLIENT_CALLBACK_ASK_NOTE, reply_markup=ReplyKeyboardRemove())


@callback_router.message(CallbackSG.waiting_note, F.text)
async def note(
    message: Message, state: FSMContext, app_user: User, session: AsyncSession
) -> None:
    raw = (message.text or "").strip()
    note_text = None if raw == "-" else raw
    data = await state.get_data()
    phone = data.get("phone", "")
    prefix = data.get("comment_prefix")
    parts = ["📞 Запрос обратного звонка"]
    if prefix:
        parts.append(prefix)
    parts.append(note_text or "без уточнений")
    try:
        payload = ClientRequestCreate(
            contact_name=app_user.full_name,
            contact_phone=phone,
            comment="\n".join(parts),
            lead_type=LeadType.CALLBACK,
        )
    except ValidationError:
        await message.answer(REQUEST_VALIDATION_FAILED, reply_markup=back_to_menu())
        await state.clear()
        return

    service = RequestService(session)
    request = await service.create_for_user(app_user.id, payload)
    await state.clear()
    await message.answer(
        CLIENT_CALLBACK_CREATED.format(id=request.id), reply_markup=back_to_menu()
    )
