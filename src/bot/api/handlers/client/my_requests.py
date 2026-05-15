from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import ClientMenuCallback, back_to_menu, requests_list_kb
from bot.api.texts import (
    REQUEST_DETAILS,
    REQUEST_LIST_HEADER,
    REQUEST_LINE,
    REQUESTS_EMPTY,
    STATUS_LABELS,
)
from bot.db.models.user import User
from bot.services.request_service import RequestService

my_requests_router = Router(name="client.my_requests")


@my_requests_router.callback_query(F.data == ClientMenuCallback.MY_REQUESTS)
async def show_my_requests(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    service = RequestService(session)
    requests = await service.list_for_user(app_user.id)
    if not requests:
        await call.message.answer(REQUESTS_EMPTY, reply_markup=back_to_menu())
        return

    lines = [REQUEST_LIST_HEADER, ""]
    for req in requests:
        lines.append(
            REQUEST_LINE.format(
                id=req.id,
                status=STATUS_LABELS.get(req.status.value, req.status.value),
                created_at=req.created_at,
            )
        )
    await call.message.answer(
        "\n".join(lines), reply_markup=requests_list_kb([r.id for r in requests])
    )


@my_requests_router.callback_query(F.data.startswith("client:req:view:"))
async def show_request_details(
    call: CallbackQuery, app_user: User, session: AsyncSession
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        request_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return

    service = RequestService(session)
    request = await service.get_for_user(app_user.id, request_id)
    if request is None:
        await call.message.answer("Заявка не найдена.", reply_markup=back_to_menu())
        return

    text = REQUEST_DETAILS.format(
        id=request.id,
        status=STATUS_LABELS.get(request.status.value, request.status.value),
        created_at=request.created_at,
        contact_name=request.contact_name,
        contact_phone=request.contact_phone,
        comment=request.comment or "—",
    )
    await call.message.answer(text, reply_markup=back_to_menu())
