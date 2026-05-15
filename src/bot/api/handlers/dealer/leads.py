from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.dealer import (
    CB_LEAD_DONE,
    CB_LEAD_REJECT,
    CB_LEAD_TAKE,
    CB_LEAD_VIEW,
    DealerMenuCallback,
    back_to_menu,
    lead_actions_kb,
    leads_list_kb,
)
from bot.api.texts import (
    DEALER_LEAD_DETAILS,
    DEALER_LEAD_NOT_FOUND,
    DEALER_LEAD_STATUS_UPDATED,
    DEALER_LEADS_EMPTY,
    DEALER_LEADS_HEADER,
    STATUS_LABELS,
)
from bot.db.models.user import User
from bot.services.dealer_lead_service import DealerLeadService

leads_router = Router(name="dealer.leads")


def _status_label(status_value: str) -> str:
    return STATUS_LABELS.get(status_value, status_value)


@leads_router.callback_query(F.data == DealerMenuCallback.LEADS)
async def show_leads(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    service = DealerLeadService(session)
    leads = await service.list_active(app_user.id)
    if not leads:
        await call.message.answer(DEALER_LEADS_EMPTY, reply_markup=back_to_menu())
        return

    lines = [DEALER_LEADS_HEADER.format(total=len(leads)), ""]
    for lead in leads:
        lines.append(
            "#{id} · {status} · {created_at:%d.%m.%Y %H:%M}".format(
                id=lead.id,
                status=_status_label(lead.status.value),
                created_at=lead.created_at,
            )
        )
        lines.append(f"   {lead.contact_name} · {lead.contact_phone}")
    await call.message.answer(
        "\n".join(lines), reply_markup=leads_list_kb([lead.id for lead in leads])
    )


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_VIEW}:"))
async def view_lead(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    lead_id = _parse_id(call.data)
    if lead_id is None:
        return
    service = DealerLeadService(session)
    lead = await service.get_for_dealer(app_user.id, lead_id)
    if lead is None:
        await call.message.answer(DEALER_LEAD_NOT_FOUND, reply_markup=back_to_menu())
        return
    text = DEALER_LEAD_DETAILS.format(
        id=lead.id,
        status=_status_label(lead.status.value),
        created_at=lead.created_at,
        contact_name=lead.contact_name,
        contact_phone=lead.contact_phone,
        comment=lead.comment or "—",
    )
    await call.message.answer(text, reply_markup=lead_actions_kb(lead.id, lead.status))


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_TAKE}:"))
async def take_lead(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await _change_status(call, app_user, session, action="take")


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_DONE}:"))
async def done_lead(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await _change_status(call, app_user, session, action="done")


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_REJECT}:"))
async def reject_lead(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await _change_status(call, app_user, session, action="reject")


async def _change_status(
    call: CallbackQuery, app_user: User, session: AsyncSession, *, action: str
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    lead_id = _parse_id(call.data)
    if lead_id is None:
        return
    service = DealerLeadService(session)
    if action == "take":
        lead = await service.take_in_progress(app_user.id, lead_id)
    elif action == "done":
        lead = await service.mark_done(app_user.id, lead_id)
    else:
        lead = await service.mark_rejected(app_user.id, lead_id)
    if lead is None:
        await call.message.answer(DEALER_LEAD_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        DEALER_LEAD_STATUS_UPDATED.format(
            id=lead.id, status=_status_label(lead.status.value)
        ),
        reply_markup=lead_actions_kb(lead.id, lead.status),
    )


def _parse_id(callback_data: str) -> int | None:
    try:
        return int(callback_data.rsplit(":", 1)[-1])
    except ValueError:
        return None
