from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.dealer import (
    CB_SERVICE_DONE,
    CB_SERVICE_REJECT,
    CB_SERVICE_TAKE,
    CB_SERVICE_VIEW,
    DealerMenuCallback,
    back_to_menu,
    service_actions_kb,
    service_list_kb,
)
from bot.api.texts import (
    DEALER_SERVICE_DETAILS,
    DEALER_SERVICE_DONE,
    DEALER_SERVICE_LINE,
    DEALER_SERVICE_LIST_EMPTY,
    DEALER_SERVICE_LIST_HEADER,
    DEALER_SERVICE_NOT_FOUND,
    DEALER_SERVICE_REJECTED,
    DEALER_SERVICE_TAKEN,
    SERVICE_ISSUE_LABELS,
    SERVICE_STATUS_LABELS,
)
from bot.db.models.user import User
from bot.services.service_request_service import ServiceRequestService

service_requests_router = Router(name="dealer.service_requests")


def _issue(value: str) -> str:
    return SERVICE_ISSUE_LABELS.get(value, value)


def _status(value: str) -> str:
    return SERVICE_STATUS_LABELS.get(value, value)


@service_requests_router.callback_query(F.data == DealerMenuCallback.SERVICE_REQUESTS)
async def show_list(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    items = await ServiceRequestService(session).list_for_dealer(app_user.id)
    if not items:
        await call.message.answer(DEALER_SERVICE_LIST_EMPTY, reply_markup=back_to_menu())
        return
    lines = [DEALER_SERVICE_LIST_HEADER.format(total=len(items)), ""]
    for r in items:
        lines.append(
            DEALER_SERVICE_LINE.format(
                id=r.id,
                issue=_issue(r.issue_type.value),
                status=_status(r.status.value),
                created_at=r.created_at,
                equipment=r.equipment or "—",
                phone=r.contact_phone,
            )
        )
    button_items = [
        (r.id, f"#{r.id} · {_issue(r.issue_type.value)} · {r.equipment or 'без модели'}")
        for r in items
    ]
    await call.message.answer("\n".join(lines), reply_markup=service_list_kb(button_items))


@service_requests_router.callback_query(F.data.startswith(f"{CB_SERVICE_VIEW}:"))
async def view(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    request_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if request_id is None:
        return
    request = await ServiceRequestService(session).get(request_id)
    if request is None:
        await call.message.answer(DEALER_SERVICE_NOT_FOUND, reply_markup=back_to_menu())
        return
    text = DEALER_SERVICE_DETAILS.format(
        id=request.id,
        issue=_issue(request.issue_type.value),
        status=_status(request.status.value),
        created_at=request.created_at,
        equipment=request.equipment or "—",
        phone=request.contact_phone,
        description=request.description,
    )
    await call.message.answer(
        text, reply_markup=service_actions_kb(request.id, request.status.value)
    )


@service_requests_router.callback_query(F.data.startswith(f"{CB_SERVICE_TAKE}:"))
async def take(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    request_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if request_id is None:
        return
    request = await ServiceRequestService(session).take(app_user.id, request_id)
    if request is None:
        await call.message.answer(DEALER_SERVICE_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        DEALER_SERVICE_TAKEN.format(id=request.id),
        reply_markup=service_actions_kb(request.id, request.status.value),
    )


@service_requests_router.callback_query(F.data.startswith(f"{CB_SERVICE_DONE}:"))
async def done(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    request_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if request_id is None:
        return
    request = await ServiceRequestService(session).mark_done(app_user.id, request_id)
    if request is None:
        await call.message.answer(DEALER_SERVICE_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        DEALER_SERVICE_DONE.format(id=request.id), reply_markup=back_to_menu()
    )


@service_requests_router.callback_query(F.data.startswith(f"{CB_SERVICE_REJECT}:"))
async def reject(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    request_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if request_id is None:
        return
    request = await ServiceRequestService(session).mark_rejected(app_user.id, request_id)
    if request is None:
        await call.message.answer(DEALER_SERVICE_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        DEALER_SERVICE_REJECTED.format(id=request.id), reply_markup=back_to_menu()
    )


def _parse_int(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None
