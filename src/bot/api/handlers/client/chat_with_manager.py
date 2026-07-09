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
from bot.api.states.client import ChatWithManagerSG
from bot.api.texts import (
    CLIENT_CHAT_ASK_PHONE,
    CLIENT_CHAT_ASK_TOPIC,
    CLIENT_CHAT_CREATED,
    CLIENT_CHAT_INTRO,
    REQUEST_VALIDATION_FAILED,
)
from bot.config import Settings
from bot.core.enums import LeadType
from bot.db.models.user import User
from bot.schemas.request import ClientRequestCreate
from bot.services.request_service import RequestService

chat_router = Router(name="client.chat_with_manager")


@chat_router.callback_query(F.data == ClientMenuCallback.CHAT)
async def start_chat(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.set_state(ChatWithManagerSG.waiting_topic)
    await call.message.answer(CLIENT_CHAT_INTRO)
    await call.message.answer(CLIENT_CHAT_ASK_TOPIC, reply_markup=cancel_kb())


@chat_router.message(ChatWithManagerSG.waiting_topic, F.text)
async def receive_topic(message: Message, state: FSMContext) -> None:
    topic = (message.text or "").strip()
    if len(topic) < 2:
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await state.update_data(topic=topic)
    await state.set_state(ChatWithManagerSG.waiting_phone)
    await message.answer(CLIENT_CHAT_ASK_PHONE, reply_markup=share_contact_kb())


@chat_router.message(ChatWithManagerSG.waiting_phone, F.contact)
async def receive_contact(
    message: Message,
    state: FSMContext,
    app_user: User,
    session: AsyncSession,
    settings: Settings,
) -> None:
    contact: Contact | None = message.contact
    if contact is None or not contact.phone_number:
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await _finalize(message, state, app_user, session, settings, phone=contact.phone_number)


@chat_router.message(ChatWithManagerSG.waiting_phone, F.text)
async def receive_phone_text(
    message: Message,
    state: FSMContext,
    app_user: User,
    session: AsyncSession,
    settings: Settings,
) -> None:
    raw = (message.text or "").strip()
    if not any(ch.isdigit() for ch in raw):
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await _finalize(message, state, app_user, session, settings, phone=raw)


async def _finalize(
    message: Message,
    state: FSMContext,
    app_user: User,
    session: AsyncSession,
    settings: Settings,
    *,
    phone: str,
) -> None:
    data = await state.get_data()
    topic = data.get("topic", "—")
    try:
        payload = ClientRequestCreate(
            contact_name=app_user.full_name,
            contact_phone=phone,
            comment=f"💬 Чат с менеджером\nТема: {topic}",
            lead_type=LeadType.CONSULTATION,
        )
    except ValidationError:
        await message.answer(REQUEST_VALIDATION_FAILED, reply_markup=back_to_menu())
        await state.clear()
        return

    service = RequestService(session, settings.bitrix)
    request = await service.create_for_user(app_user.id, payload)
    await state.clear()
    await message.answer(
        CLIENT_CHAT_CREATED.format(id=request.id),
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Главное меню:", reply_markup=back_to_menu())
