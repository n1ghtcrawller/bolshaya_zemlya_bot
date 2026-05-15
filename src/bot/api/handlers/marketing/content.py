from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import cancel_kb
from bot.api.keyboards.marketing import (
    CB_CONTENT_NEW,
    CB_CONTENT_TYPE,
    MktMenuCallback,
    back_to_menu,
    content_new_type_kb,
    content_types_kb,
)
from bot.api.states.marketing import ContentCreateSG
from bot.api.texts import (
    CONTENT_STATUS_LABELS,
    CONTENT_TYPE_LABELS,
    MKT_CONTENT_ASK_BODY,
    MKT_CONTENT_ASK_REGION,
    MKT_CONTENT_ASK_SCHEDULED,
    MKT_CONTENT_ASK_TITLE,
    MKT_CONTENT_CREATED,
    MKT_CONTENT_DATE_INVALID,
    MKT_CONTENT_LIST_EMPTY,
    MKT_CONTENT_LIST_HEADER,
    MKT_CONTENT_PICK_TYPE,
)
from bot.core.enums import ContentType
from bot.db.models.user import User
from bot.services.content_service import ContentService

content_router = Router(name="marketing.content")

DATE_FORMATS = ("%d.%m.%Y %H:%M", "%d.%m.%Y")


@content_router.callback_query(F.data == MktMenuCallback.CONTENT)
async def show_content_menu(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.clear()
    await call.message.answer(MKT_CONTENT_PICK_TYPE, reply_markup=content_types_kb())


@content_router.callback_query(F.data.startswith(f"{CB_CONTENT_TYPE}:"))
async def list_by_type(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    content_type = _parse_type(call.data.rsplit(":", 1)[-1])
    if content_type is None:
        return
    items = await ContentService(session).list_by_type(content_type)
    header = MKT_CONTENT_LIST_HEADER.format(
        type_label=CONTENT_TYPE_LABELS[content_type.value], total=len(items)
    )
    if not items:
        await call.message.answer(f"{header}\n\n{MKT_CONTENT_LIST_EMPTY}", reply_markup=back_to_menu())
        return
    lines = [header, ""]
    for item in items:
        status = CONTENT_STATUS_LABELS.get(item.status.value, item.status.value)
        lines.append(f"#{item.id} · {status} · {item.title}")
        if item.region:
            lines.append(f"   📍 {item.region}")
        if item.scheduled_at:
            lines.append(f"   ⏰ {item.scheduled_at:%d.%m.%Y %H:%M}")
    await call.message.answer("\n".join(lines), reply_markup=back_to_menu())


@content_router.callback_query(F.data == CB_CONTENT_NEW)
async def start_new(call: CallbackQuery) -> None:
    await call.answer()
    if call.message is None:
        return
    await call.message.answer("Тип новой записи:", reply_markup=content_new_type_kb())


@content_router.callback_query(F.data.startswith(f"{CB_CONTENT_NEW}:"))
async def pick_new_type(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    content_type = _parse_type(call.data.rsplit(":", 1)[-1])
    if content_type is None:
        return
    await state.set_state(ContentCreateSG.waiting_title)
    await state.update_data(type=content_type.value)
    await call.message.answer(MKT_CONTENT_ASK_TITLE, reply_markup=cancel_kb())


@content_router.message(ContentCreateSG.waiting_title, F.text)
async def receive_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer(MKT_CONTENT_ASK_TITLE)
        return
    await state.update_data(title=title)
    await state.set_state(ContentCreateSG.waiting_body)
    await message.answer(MKT_CONTENT_ASK_BODY)


@content_router.message(ContentCreateSG.waiting_body, F.text)
async def receive_body(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    body = None if raw == "-" else raw
    await state.update_data(body=body)
    await state.set_state(ContentCreateSG.waiting_region)
    await message.answer(MKT_CONTENT_ASK_REGION)


@content_router.message(ContentCreateSG.waiting_region, F.text)
async def receive_region(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    region = None if raw == "-" else raw
    await state.update_data(region=region)
    await state.set_state(ContentCreateSG.waiting_scheduled)
    await message.answer(MKT_CONTENT_ASK_SCHEDULED)


@content_router.message(ContentCreateSG.waiting_scheduled, F.text)
async def receive_scheduled(
    message: Message, state: FSMContext, app_user: User, session: AsyncSession
) -> None:
    raw = (message.text or "").strip()
    scheduled_at: datetime | None = None
    if raw != "-":
        scheduled_at = _parse_date(raw)
        if scheduled_at is None:
            await message.answer(MKT_CONTENT_DATE_INVALID)
            return
    data = await state.get_data()
    service = ContentService(session)
    item = await service.create(
        content_type=ContentType(data["type"]),
        title=data["title"],
        body=data.get("body"),
        region=data.get("region"),
        scheduled_at=scheduled_at,
        author_user_id=app_user.id,
    )
    await state.clear()
    await message.answer(
        MKT_CONTENT_CREATED.format(id=item.id, title=item.title),
        reply_markup=back_to_menu(),
    )


def _parse_type(raw: str) -> ContentType | None:
    try:
        return ContentType(raw)
    except ValueError:
        return None


def _parse_date(raw: str) -> datetime | None:
    for fmt in DATE_FORMATS:
        try:
            naive = datetime.strptime(raw, fmt)
        except ValueError:
            continue
        return naive.replace(tzinfo=timezone.utc)
    return None
