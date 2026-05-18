from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.handlers.sales._dealer_card import render_dealer_card
from bot.api.keyboards.sales import (
    CB_DIRECTORY_DEALER,
    CB_LEAD_KEEP,
    CB_LEAD_REJECT,
    CB_LEAD_REQUEST_APPROVAL,
    CB_LEAD_TAKE,
    CB_LEAD_TRANSFER_CONFIRM,
    CB_LEAD_TRANSFER_REGION,
    CB_LEAD_VIEW,
    SalesMenuCallback,
    back_to_menu,
    dealers_kb,
    lead_actions_kb,
    leads_list_kb,
    region_token,
    regions_kb,
)
from bot.api.texts import (
    LEAD_TYPE_LABELS,
    SALES_LEAD_ALREADY_TAKEN,
    SALES_LEAD_DETAILS,
    SALES_LEAD_NOT_FOUND,
    SALES_LEAD_REJECTED,
    SALES_LEAD_TAKEN,
    SALES_LEAD_TRANSFER_DONE,
    SALES_LEAD_TRANSFER_NO_DEALERS,
    SALES_LEAD_TRANSFER_NO_REGIONS,
    SALES_LEAD_TRANSFER_NOT_OWNER,
    SALES_LEAD_TRANSFER_PICK_DEALER,
    SALES_LEAD_TRANSFER_PICK_REGION,
    SALES_LEADS_IN_PROGRESS_EMPTY,
    SALES_LEADS_IN_PROGRESS_HEADER,
    SALES_LEADS_NEW_EMPTY,
    SALES_LEADS_NEW_HEADER,
    SALES_LEADS_TRANSFERRED_EMPTY,
    SALES_LEADS_TRANSFERRED_HEADER,
    STATUS_LABELS,
)
from bot.core.enums import RequestStatus
from bot.db.models.user import User
from bot.services.dealer_directory_service import DealerDirectoryService
from bot.services.sales_lead_service import SalesLeadService

leads_router = Router(name="sales.leads")


def _status_label(status_value: str) -> str:
    return STATUS_LABELS.get(status_value, status_value)


def _lead_type_label(value: str) -> str:
    return LEAD_TYPE_LABELS.get(value, value)


def _render_short(lead) -> str:
    return (
        f"#{lead.id} · {_lead_type_label(lead.lead_type.value)} · "
        f"{_status_label(lead.status.value)} · "
        f"{lead.created_at:%d.%m.%Y %H:%M}\n"
        f"   {lead.contact_name} · {lead.contact_phone}"
    )


@leads_router.callback_query(F.data == SalesMenuCallback.LEADS_NEW)
async def list_new(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    service = SalesLeadService(session)
    leads = await service.list_new()
    if not leads:
        await call.message.answer(SALES_LEADS_NEW_EMPTY, reply_markup=back_to_menu())
        return
    text = [SALES_LEADS_NEW_HEADER.format(total=len(leads)), ""]
    for lead in leads:
        text.append(_render_short(lead))
    await call.message.answer(
        "\n".join(text),
        reply_markup=leads_list_kb([l.id for l in leads], back=SalesMenuCallback.BACK_TO_MENU),
    )


@leads_router.callback_query(F.data == SalesMenuCallback.LEADS_IN_PROGRESS)
async def list_in_progress(
    call: CallbackQuery, app_user: User, session: AsyncSession
) -> None:
    await call.answer()
    if call.message is None:
        return
    service = SalesLeadService(session)
    leads = await service.list_in_progress(app_user.id)
    if not leads:
        await call.message.answer(SALES_LEADS_IN_PROGRESS_EMPTY, reply_markup=back_to_menu())
        return
    text = [SALES_LEADS_IN_PROGRESS_HEADER.format(total=len(leads)), ""]
    for lead in leads:
        text.append(_render_short(lead))
    await call.message.answer(
        "\n".join(text),
        reply_markup=leads_list_kb([l.id for l in leads], back=SalesMenuCallback.BACK_TO_MENU),
    )


@leads_router.callback_query(F.data == SalesMenuCallback.LEADS_TRANSFERRED)
async def list_transferred(
    call: CallbackQuery, app_user: User, session: AsyncSession
) -> None:
    await call.answer()
    if call.message is None:
        return
    service = SalesLeadService(session)
    leads = await service.list_transferred(app_user.id)
    if not leads:
        await call.message.answer(SALES_LEADS_TRANSFERRED_EMPTY, reply_markup=back_to_menu())
        return
    text = [SALES_LEADS_TRANSFERRED_HEADER.format(total=len(leads)), ""]
    for lead in leads:
        text.append(_render_short(lead))
    await call.message.answer(
        "\n".join(text),
        reply_markup=leads_list_kb([l.id for l in leads], back=SalesMenuCallback.BACK_TO_MENU),
    )


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_VIEW}:"))
async def view_lead(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    lead_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if lead_id is None:
        return
    service = SalesLeadService(session)
    lead = await service.get(lead_id)
    if lead is None:
        await call.message.answer(SALES_LEAD_NOT_FOUND, reply_markup=back_to_menu())
        return
    text = SALES_LEAD_DETAILS.format(
        id=lead.id,
        status=f"{_lead_type_label(lead.lead_type.value)} · {_status_label(lead.status.value)}",
        created_at=lead.created_at,
        contact_name=lead.contact_name,
        contact_phone=lead.contact_phone,
        comment=lead.comment or "—",
    )
    await call.message.answer(text, reply_markup=lead_actions_kb(lead.id, lead.status))


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_TAKE}:"))
async def take_lead(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    lead_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if lead_id is None:
        return
    service = SalesLeadService(session)
    lead = await service.take(app_user.id, lead_id)
    if lead is None:
        await call.message.answer(SALES_LEAD_NOT_FOUND, reply_markup=back_to_menu())
        return
    if lead.assigned_sales_id != app_user.id:
        await call.message.answer(SALES_LEAD_ALREADY_TAKEN, reply_markup=back_to_menu())
        return
    await call.message.answer(
        SALES_LEAD_TAKEN.format(id=lead.id),
        reply_markup=lead_actions_kb(lead.id, lead.status),
    )


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_REJECT}:"))
async def reject_lead(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    lead_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if lead_id is None:
        return
    service = SalesLeadService(session)
    lead = await service.reject(app_user.id, lead_id)
    if lead is None:
        await call.message.answer(SALES_LEAD_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        SALES_LEAD_REJECTED.format(id=lead.id), reply_markup=back_to_menu()
    )


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_TRANSFER_REGION}:"))
async def pick_region(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    lead_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if lead_id is None:
        return
    leads_service = SalesLeadService(session)
    lead = await leads_service.get(lead_id)
    if lead is None or lead.assigned_sales_id != app_user.id:
        await call.message.answer(SALES_LEAD_TRANSFER_NOT_OWNER, reply_markup=back_to_menu())
        return
    if lead.status != RequestStatus.IN_PROGRESS:
        await call.message.answer(SALES_LEAD_TRANSFER_NOT_OWNER, reply_markup=back_to_menu())
        return

    directory = DealerDirectoryService(session)
    regions = await directory.list_regions()
    if not regions:
        await call.message.answer(
            SALES_LEAD_TRANSFER_NO_REGIONS, reply_markup=back_to_menu()
        )
        return
    await call.message.answer(
        SALES_LEAD_TRANSFER_PICK_REGION,
        reply_markup=regions_kb(
            list(regions), callback_prefix="sales:lead:transfer:r", lead_id=lead_id
        ),
    )


@leads_router.callback_query(F.data.startswith("sales:lead:transfer:r:"))
async def pick_dealer(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    parts = call.data.split(":")
    if len(parts) != 6:
        return
    lead_id = _parse_int(parts[-2])
    token = parts[-1]
    if lead_id is None:
        return
    directory = DealerDirectoryService(session)
    regions = await directory.list_regions()
    region = next((r for r in regions if region_token(r) == token), None)
    if region is None:
        await call.message.answer(SALES_LEAD_TRANSFER_NO_REGIONS, reply_markup=back_to_menu())
        return
    dealers = await directory.list_by_region(region)
    if not dealers:
        await call.message.answer(SALES_LEAD_TRANSFER_NO_DEALERS, reply_markup=back_to_menu())
        return
    options: list[tuple[int, str]] = []
    for user, profile in dealers:
        label = user.full_name
        if profile and profile.company:
            label = f"{user.full_name} · {profile.company}"
        options.append((user.id, label))
    await call.message.answer(
        SALES_LEAD_TRANSFER_PICK_DEALER.format(region=region),
        reply_markup=dealers_kb(options, lead_id=lead_id),
    )


@leads_router.callback_query(F.data.startswith(f"{CB_DIRECTORY_DEALER}:"))
async def show_dealer_card(call: CallbackQuery, session: AsyncSession) -> None:
    """Открытие карточки диллера. Если lead_id != 0 — в режиме передачи лида."""
    await call.answer()
    if call.message is None or call.data is None:
        return
    parts = call.data.split(":")
    if len(parts) != 5:
        return
    lead_id = _parse_int(parts[-2])
    dealer_id = _parse_int(parts[-1])
    if dealer_id is None:
        return
    directory = DealerDirectoryService(session)
    dealer = await directory.get_dealer(dealer_id)
    await render_dealer_card(
        call,
        dealer=dealer,
        lead_id=lead_id if lead_id else None,
        session=session,
    )


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_TRANSFER_CONFIRM}:"))
async def transfer_confirm(
    call: CallbackQuery, app_user: User, session: AsyncSession
) -> None:
    """Подтверждение передачи лида диллеру из карточки диллера."""
    await call.answer()
    if call.message is None or call.data is None:
        return
    parts = call.data.split(":")
    if len(parts) != 6:
        return
    lead_id = _parse_int(parts[-2])
    dealer_id = _parse_int(parts[-1])
    if lead_id is None or dealer_id is None:
        return
    service = SalesLeadService(session)
    lead = await service.transfer_to_dealer(app_user.id, lead_id, dealer_id)
    if lead is None:
        await call.message.answer(SALES_LEAD_TRANSFER_NOT_OWNER, reply_markup=back_to_menu())
        return
    directory = DealerDirectoryService(session)
    dealer = await directory.get_dealer(dealer_id)
    dealer_name = dealer[0].full_name if dealer else f"#{dealer_id}"
    await call.message.answer(
        SALES_LEAD_TRANSFER_DONE.format(id=lead.id, dealer_name=dealer_name),
        reply_markup=back_to_menu(),
    )


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_REQUEST_APPROVAL}:"))
async def request_head_approval(
    call: CallbackQuery, app_user: User, session: AsyncSession
) -> None:
    """Sales отправляет передачу лида диллеру на согласование HeadOfSales."""
    from bot.api.texts import (
        SALES_LEAD_APPROVAL_DUPLICATE,
        SALES_LEAD_APPROVAL_REQUESTED,
    )
    from bot.services.lead_approval_service import LeadApprovalService

    await call.answer()
    if call.message is None or call.data is None:
        return
    parts = call.data.split(":")
    if len(parts) != 5:
        return
    lead_id = _parse_int(parts[-2])
    dealer_id = _parse_int(parts[-1])
    if lead_id is None or dealer_id is None:
        return
    service = LeadApprovalService(session)
    approval, error = await service.request(
        sales_user_id=app_user.id, lead_id=lead_id, proposed_dealer_id=dealer_id
    )
    if error == "duplicate_pending":
        await call.message.answer(SALES_LEAD_APPROVAL_DUPLICATE, reply_markup=back_to_menu())
        return
    if approval is None:
        await call.message.answer(SALES_LEAD_TRANSFER_NOT_OWNER, reply_markup=back_to_menu())
        return
    await call.message.answer(
        SALES_LEAD_APPROVAL_REQUESTED.format(id=approval.id, lead_id=lead_id),
        reply_markup=back_to_menu(),
    )


@leads_router.callback_query(F.data.startswith(f"{CB_LEAD_KEEP}:"))
async def keep_lead(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    """Sales решает оставить лид у себя (не передавать диллеру)."""
    await call.answer()
    if call.message is None or call.data is None:
        return
    lead_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if lead_id is None:
        return
    service = SalesLeadService(session)
    lead = await service.keep(app_user.id, lead_id)
    if lead is None:
        await call.message.answer(SALES_LEAD_TRANSFER_NOT_OWNER, reply_markup=back_to_menu())
        return
    from bot.api.texts import SALES_LEAD_KEPT

    await call.message.answer(
        SALES_LEAD_KEPT.format(id=lead.id), reply_markup=back_to_menu()
    )


def _parse_int(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None
