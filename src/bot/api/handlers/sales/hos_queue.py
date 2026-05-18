"""Очередь согласований передач лидов — для HeadOfSales.

Видна только пользователям с ролью HEAD_OF_SALES. Регистрируется в sales-роутере
(RoleFilter включает обе роли), но обработчики дополнительно проверяют роль.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.sales import (
    CB_HOS_APPROVE,
    CB_HOS_REJECT,
    CB_HOS_VIEW,
    SalesMenuCallback,
    back_to_menu,
    hos_approval_actions_kb,
    hos_queue_list_kb,
)
from bot.api.texts import (
    HOS_APPROVAL_ALREADY_DECIDED,
    HOS_APPROVAL_DETAILS,
    HOS_APPROVAL_DONE,
    HOS_APPROVAL_NOT_FOUND,
    HOS_APPROVAL_REJECTED,
    HOS_QUEUE_EMPTY,
    HOS_QUEUE_HEADER,
    HOS_QUEUE_LINE,
)
from bot.core.enums import UserRole
from bot.db.models.user import User
from bot.db.repositories.client_request import ClientRequestRepository
from bot.services.lead_approval_service import LeadApprovalService

hos_queue_router = Router(name="sales.hos_queue")


def _is_head(user: User) -> bool:
    return user.role is UserRole.HEAD_OF_SALES


@hos_queue_router.callback_query(F.data == SalesMenuCallback.HOS_QUEUE)
async def show_queue(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    if not _is_head(app_user):
        await call.message.answer(HOS_APPROVAL_NOT_FOUND, reply_markup=back_to_menu())
        return
    items = await LeadApprovalService(session).list_pending()
    if not items:
        await call.message.answer(HOS_QUEUE_EMPTY, reply_markup=back_to_menu())
        return
    lines = [HOS_QUEUE_HEADER.format(total=len(items)), ""]
    for a in items:
        lines.append(
            HOS_QUEUE_LINE.format(
                id=a.id,
                lead_id=a.lead_id,
                sales_id=a.sales_user_id,
                dealer_id=a.proposed_dealer_id,
            )
        )
    await call.message.answer(
        "\n".join(lines), reply_markup=hos_queue_list_kb([a.id for a in items])
    )


@hos_queue_router.callback_query(F.data.startswith(f"{CB_HOS_VIEW}:"))
async def view_approval(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    if not _is_head(app_user):
        return
    approval_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if approval_id is None:
        return
    service = LeadApprovalService(session)
    approval = await service.get(approval_id)
    if approval is None:
        await call.message.answer(HOS_APPROVAL_NOT_FOUND, reply_markup=back_to_menu())
        return
    lead = await ClientRequestRepository(session).get_by_id(approval.lead_id)
    text = HOS_APPROVAL_DETAILS.format(
        id=approval.id,
        created_at=approval.created_at,
        lead_id=approval.lead_id,
        contact_name=lead.contact_name if lead else "—",
        contact_phone=lead.contact_phone if lead else "—",
        sales_id=approval.sales_user_id,
        dealer_id=approval.proposed_dealer_id,
        lead_comment=(lead.comment if lead and lead.comment else "—"),
    )
    await call.message.answer(text, reply_markup=hos_approval_actions_kb(approval.id))


@hos_queue_router.callback_query(F.data.startswith(f"{CB_HOS_APPROVE}:"))
async def approve(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await _decide(call, app_user, session, action="approve")


@hos_queue_router.callback_query(F.data.startswith(f"{CB_HOS_REJECT}:"))
async def reject(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await _decide(call, app_user, session, action="reject")


async def _decide(
    call: CallbackQuery, app_user: User, session: AsyncSession, *, action: str
) -> None:
    await call.answer()
    if call.message is None or call.data is None or not _is_head(app_user):
        return
    approval_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if approval_id is None:
        return
    service = LeadApprovalService(session)
    if action == "approve":
        approval, error = await service.approve(approval_id, head_user_id=app_user.id)
    else:
        approval, error = await service.reject(approval_id, head_user_id=app_user.id)
    if approval is None:
        await call.message.answer(HOS_APPROVAL_NOT_FOUND, reply_markup=back_to_menu())
        return
    if error == "already_decided":
        await call.message.answer(HOS_APPROVAL_ALREADY_DECIDED, reply_markup=back_to_menu())
        return
    if action == "approve":
        await call.message.answer(
            HOS_APPROVAL_DONE.format(id=approval.id, lead_id=approval.lead_id),
            reply_markup=back_to_menu(),
        )
    else:
        await call.message.answer(
            HOS_APPROVAL_REJECTED.format(id=approval.id), reply_markup=back_to_menu()
        )


def _parse_int(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None
