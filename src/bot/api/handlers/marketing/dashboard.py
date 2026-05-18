from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.marketing import (
    CB_DASH_DEALERS,
    CB_DASH_PRODUCTS,
    CB_DASH_SUMMARY,
    MktMenuCallback,
    back_to_menu,
    dashboard_menu_kb,
)
from bot.api.texts import (
    MKT_DASHBOARD_DEALER_LINE,
    MKT_DASHBOARD_DEALERS_EMPTY,
    MKT_DASHBOARD_DEALERS_HEADER,
    MKT_DASHBOARD_EMPTY_LEADS,
    MKT_DASHBOARD_EMPTY_USERS,
    MKT_DASHBOARD_MENU,
    MKT_DASHBOARD_PRODUCT_LINE,
    MKT_DASHBOARD_PRODUCTS_EMPTY,
    MKT_DASHBOARD_PRODUCTS_HEADER,
    MKT_DASHBOARD_TEMPLATE,
    ROLE_LABELS,
    STATUS_LABELS,
)
from bot.services.dashboard_service import DashboardService

dashboard_router = Router(name="marketing.dashboard")


@dashboard_router.callback_query(F.data == MktMenuCallback.DASHBOARD)
async def show_dashboard_menu(call: CallbackQuery) -> None:
    await call.answer()
    if call.message is None:
        return
    await call.message.answer(MKT_DASHBOARD_MENU, reply_markup=dashboard_menu_kb())


@dashboard_router.callback_query(F.data == CB_DASH_SUMMARY)
async def show_summary(call: CallbackQuery, session: AsyncSession) -> None:
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
        reply_markup=dashboard_menu_kb(),
    )


@dashboard_router.callback_query(F.data == CB_DASH_DEALERS)
async def show_dealers(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    rows = await DashboardService(session).dealers_breakdown(top_n=10)
    if not rows:
        await call.message.answer(MKT_DASHBOARD_DEALERS_EMPTY, reply_markup=back_to_menu())
        return
    lines = [MKT_DASHBOARD_DEALERS_HEADER.format(total=len(rows)), ""]
    for r in rows:
        lines.append(
            MKT_DASHBOARD_DEALER_LINE.format(
                id=r.dealer_id,
                full_name=r.full_name,
                company_suffix=f" · {r.company}" if r.company else "",
                total=r.total,
                in_progress=r.in_progress,
                done=r.done,
                rejected=r.rejected,
                transferred=r.transferred,
            )
        )
    await call.message.answer("\n".join(lines), reply_markup=dashboard_menu_kb())


@dashboard_router.callback_query(F.data == CB_DASH_PRODUCTS)
async def show_products(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    rows = await DashboardService(session).top_products(top_n=10)
    if not rows:
        await call.message.answer(MKT_DASHBOARD_PRODUCTS_EMPTY, reply_markup=back_to_menu())
        return
    lines = [MKT_DASHBOARD_PRODUCTS_HEADER.format(total=len(rows)), ""]
    for r in rows:
        lines.append(
            MKT_DASHBOARD_PRODUCT_LINE.format(
                id=r.product_id,
                name=r.name,
                category=r.category,
                total=r.requests_total,
            )
        )
    await call.message.answer("\n".join(lines), reply_markup=dashboard_menu_kb())
