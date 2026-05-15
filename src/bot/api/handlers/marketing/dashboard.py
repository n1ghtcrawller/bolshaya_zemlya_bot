from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.marketing import MktMenuCallback, back_to_menu
from bot.api.texts import (
    MKT_DASHBOARD_EMPTY_LEADS,
    MKT_DASHBOARD_EMPTY_USERS,
    MKT_DASHBOARD_TEMPLATE,
    ROLE_LABELS,
    STATUS_LABELS,
)
from bot.services.dashboard_service import DashboardService

dashboard_router = Router(name="marketing.dashboard")


@dashboard_router.callback_query(F.data == MktMenuCallback.DASHBOARD)
async def show_dashboard(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    snapshot = await DashboardService(session).snapshot()

    users_block = (
        "\n".join(
            f"• {ROLE_LABELS.get(role.value, role.value)}: {count}"
            for role, count in snapshot.users_by_role.items()
        )
        or MKT_DASHBOARD_EMPTY_USERS
    )
    leads_block = (
        "\n".join(
            f"• {STATUS_LABELS.get(status.value, status.value)}: {count}"
            for status, count in snapshot.leads_by_status.items()
        )
        or MKT_DASHBOARD_EMPTY_LEADS
    )

    await call.message.answer(
        MKT_DASHBOARD_TEMPLATE.format(users_block=users_block, leads_block=leads_block),
        reply_markup=back_to_menu(),
    )
