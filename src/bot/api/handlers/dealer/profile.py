from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.dealer import (
    CB_PROFILE_EDIT,
    DealerMenuCallback,
    back_to_menu,
    profile_edit_kb,
)
from bot.api.states.dealer import DealerProfileEditSG
from bot.api.texts import (
    DEALER_PROFILE_ASK_ADDRESS,
    DEALER_PROFILE_ASK_COMPANY,
    DEALER_PROFILE_ASK_DESCRIPTION,
    DEALER_PROFILE_ASK_PHONE,
    DEALER_PROFILE_ASK_REGION,
    DEALER_PROFILE_ASK_SPECIALIZATION,
    DEALER_PROFILE_EDIT_HINT,
    DEALER_PROFILE_EMPTY_VALUE,
    DEALER_PROFILE_FIELD_SAVED,
    DEALER_PROFILE_TEMPLATE,
)
from bot.db.models.user import User
from bot.services.dealer_service import DealerService

profile_router = Router(name="dealer.profile")

FIELD_PROMPTS: dict[str, str] = {
    "phone": DEALER_PROFILE_ASK_PHONE,
    "company": DEALER_PROFILE_ASK_COMPANY,
    "region": DEALER_PROFILE_ASK_REGION,
    "address": DEALER_PROFILE_ASK_ADDRESS,
    "description": DEALER_PROFILE_ASK_DESCRIPTION,
    "specialization": DEALER_PROFILE_ASK_SPECIALIZATION,
}


@profile_router.callback_query(F.data == DealerMenuCallback.PROFILE)
async def show_profile(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    service = DealerService(session)
    profile = await service.get_profile(app_user.id)

    def fmt(value: str | None) -> str:
        return value or DEALER_PROFILE_EMPTY_VALUE

    text = DEALER_PROFILE_TEMPLATE.format(
        full_name=app_user.full_name,
        company=fmt(profile.company if profile else None),
        region=fmt(profile.region if profile else None),
        address=fmt(profile.address if profile else None),
        phone=fmt(profile.phone if profile else None),
        specialization=fmt(profile.specialization if profile else None),
        description=fmt(profile.description if profile else None),
    )
    await call.message.answer(text, reply_markup=profile_edit_kb())
    await call.message.answer(DEALER_PROFILE_EDIT_HINT)


@profile_router.callback_query(F.data.startswith(f"{CB_PROFILE_EDIT}:"))
async def start_edit_field(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    field = call.data.rsplit(":", 1)[-1]
    prompt = FIELD_PROMPTS.get(field)
    if prompt is None:
        return
    await state.set_state(DealerProfileEditSG.waiting_value)
    await state.update_data(field=field)
    await call.message.answer(prompt)


@profile_router.message(DealerProfileEditSG.waiting_value, F.text)
async def receive_value(
    message: Message, app_user: User, session: AsyncSession, state: FSMContext
) -> None:
    data = await state.get_data()
    field = data.get("field")
    if field not in FIELD_PROMPTS:
        await state.clear()
        return
    raw = (message.text or "").strip()
    value: str | None = None if raw == "-" else raw
    service = DealerService(session)
    await service.update_fields(app_user.id, {field: value})
    await state.clear()
    await message.answer(DEALER_PROFILE_FIELD_SAVED, reply_markup=back_to_menu())
