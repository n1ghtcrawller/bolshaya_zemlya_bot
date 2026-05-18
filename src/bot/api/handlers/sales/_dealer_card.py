"""Общий рендер карточки диллера для Sales (используется find_dealer и leads)."""
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.sales import dealer_card_actions_kb, dealer_tg_url
from bot.api.texts import (
    SALES_DEALER_CARD,
    SALES_DEALER_CARD_HEADER_DIRECTORY,
    SALES_DEALER_CARD_HEADER_FOR_LEAD,
    SALES_DEALER_CARD_NO_USERNAME,
    SALES_DEALER_NOT_FOUND,
    SALES_DEALER_STATUS_ACTIVE,
    SALES_DEALER_STATUS_INACTIVE,
)
from bot.core.enums import UserRole
from bot.db.models.dealer_profile import DealerProfile
from bot.db.models.user import User
from bot.db.repositories.user import UserRepository


async def render_dealer_card(
    call: CallbackQuery,
    *,
    dealer: tuple[User, DealerProfile | None] | None,
    lead_id: int | None,
    session: AsyncSession,
) -> None:
    """Отрисовать карточку диллера. Если dealer is None — показать «не найдено».

    Если lead_id указан — заголовок и действия настроены под передачу лида.
    Кнопка «👔 Запросить согласование» появится, только если в БД есть head_of_sales.
    """
    if call.message is None:
        return
    if dealer is None:
        from bot.api.keyboards.sales import back_to_menu

        await call.message.answer(SALES_DEALER_NOT_FOUND, reply_markup=back_to_menu())
        return

    user, profile = dealer
    header = (
        SALES_DEALER_CARD_HEADER_FOR_LEAD.format(lead_id=lead_id)
        if lead_id is not None
        else SALES_DEALER_CARD_HEADER_DIRECTORY
    )
    status_label = (
        SALES_DEALER_STATUS_ACTIVE if user.is_active else SALES_DEALER_STATUS_INACTIVE
    )
    body = SALES_DEALER_CARD.format(
        full_name=user.full_name,
        company=(profile.company if profile else None) or "—",
        region=(profile.region if profile else None) or "—",
        address=(profile.address if profile else None) or "—",
        phone=(profile.phone if profile else None) or "—",
        username=user.username or SALES_DEALER_CARD_NO_USERNAME,
        status=status_label,
        specialization=(profile.specialization if profile else None) or "—",
        description=(profile.description if profile else None) or "—",
    )
    head_available = False
    if lead_id is not None:
        head_available = await UserRepository(session).has_role(UserRole.HEAD_OF_SALES)
    keyboard = dealer_card_actions_kb(
        dealer_id=user.id,
        lead_id=lead_id,
        tg_url=dealer_tg_url(username=user.username, telegram_id=user.telegram_id),
        head_available=head_available,
    )
    await call.message.answer(f"{header}\n\n{body}", reply_markup=keyboard)
