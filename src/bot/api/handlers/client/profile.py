from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import ClientMenuCallback, back_to_menu
from bot.api.texts import PROFILE_EMPTY_VALUE, PROFILE_TEMPLATE
from bot.db.models.user import User
from bot.db.repositories.client_profile import ClientProfileRepository

profile_router = Router(name="client.profile")


@profile_router.callback_query(F.data == ClientMenuCallback.PROFILE)
async def show_profile(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return

    repo = ClientProfileRepository(session)
    profile = await repo.get_by_user_id(app_user.id)

    def fmt(value: str | None) -> str:
        return value or PROFILE_EMPTY_VALUE

    text = PROFILE_TEMPLATE.format(
        full_name=app_user.full_name,
        phone=fmt(profile.phone if profile else None),
        region=fmt(profile.region if profile else None),
        company=fmt(profile.company if profile else None),
        email=fmt(profile.email if profile else None),
    )
    await call.message.answer(text, reply_markup=back_to_menu())
