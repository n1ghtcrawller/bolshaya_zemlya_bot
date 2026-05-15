from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Contact, Message, ReplyKeyboardRemove
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import (
    ClientMenuCallback,
    back_to_menu,
    cancel_kb,
    service_issue_types_kb,
    share_contact_kb,
)
from bot.api.states.client import ServiceRequestSG
from bot.api.texts import (
    CLIENT_SERVICE_ASK_DESCRIPTION,
    CLIENT_SERVICE_ASK_EQUIPMENT,
    CLIENT_SERVICE_ASK_PHONE,
    CLIENT_SERVICE_CREATED,
    CLIENT_SERVICE_INTRO,
    REQUEST_VALIDATION_FAILED,
)
from bot.core.enums import ServiceIssueType
from bot.db.models.user import User
from bot.schemas.request import ServiceRequestCreate
from bot.services.service_request_service import ServiceRequestService

service_router = Router(name="client.service")


@service_router.callback_query(F.data == ClientMenuCallback.SERVICE)
async def start_service(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.set_state(ServiceRequestSG.waiting_issue)
    await call.message.answer(CLIENT_SERVICE_INTRO, reply_markup=service_issue_types_kb())


@service_router.callback_query(
    ServiceRequestSG.waiting_issue, F.data.startswith("client:srv:issue:")
)
async def pick_issue(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    raw = call.data.rsplit(":", 1)[-1]
    try:
        issue = ServiceIssueType(raw)
    except ValueError:
        return
    await state.update_data(issue=issue.value)
    await state.set_state(ServiceRequestSG.waiting_equipment)
    await call.message.answer(CLIENT_SERVICE_ASK_EQUIPMENT, reply_markup=cancel_kb())


@service_router.message(ServiceRequestSG.waiting_equipment, F.text)
async def equipment(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    equipment_value = None if raw == "-" else raw
    await state.update_data(equipment=equipment_value)
    await state.set_state(ServiceRequestSG.waiting_description)
    await message.answer(CLIENT_SERVICE_ASK_DESCRIPTION)


@service_router.message(ServiceRequestSG.waiting_description, F.text)
async def description(message: Message, state: FSMContext) -> None:
    desc = (message.text or "").strip()
    if len(desc) < 2:
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await state.update_data(description=desc)
    await state.set_state(ServiceRequestSG.waiting_phone)
    await message.answer(CLIENT_SERVICE_ASK_PHONE, reply_markup=share_contact_kb())


@service_router.message(ServiceRequestSG.waiting_phone, F.contact)
async def phone_contact(
    message: Message, state: FSMContext, app_user: User, session: AsyncSession
) -> None:
    contact: Contact | None = message.contact
    if contact is None or not contact.phone_number:
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await _finalize(message, state, app_user, session, phone=contact.phone_number)


@service_router.message(ServiceRequestSG.waiting_phone, F.text)
async def phone_text(
    message: Message, state: FSMContext, app_user: User, session: AsyncSession
) -> None:
    raw = (message.text or "").strip()
    if not any(ch.isdigit() for ch in raw):
        await message.answer(REQUEST_VALIDATION_FAILED)
        return
    await _finalize(message, state, app_user, session, phone=raw)


async def _finalize(
    message: Message,
    state: FSMContext,
    app_user: User,
    session: AsyncSession,
    *,
    phone: str,
) -> None:
    data = await state.get_data()
    try:
        payload = ServiceRequestCreate(
            issue_type=data.get("issue", "other"),
            equipment=data.get("equipment"),
            description=data["description"],
            contact_phone=phone,
        )
    except (ValidationError, KeyError):
        await message.answer(REQUEST_VALIDATION_FAILED, reply_markup=back_to_menu())
        await state.clear()
        return

    service = ServiceRequestService(session)
    request = await service.create_for_user(app_user.id, payload)
    await state.clear()
    await message.answer(
        CLIENT_SERVICE_CREATED.format(id=request.id), reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Главное меню:", reply_markup=back_to_menu())
