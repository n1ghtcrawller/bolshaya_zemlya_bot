from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import cancel_kb
from bot.api.keyboards.marketing import (
    CB_CONTENT_APPROVE,
    CB_CONTENT_ARCHIVE,
    CB_CONTENT_NEW,
    CB_CONTENT_PENDING,
    CB_CONTENT_PUBLISH,
    CB_CONTENT_REJECT,
    CB_CONTENT_SUBMIT_CHOICE,
    CB_CONTENT_SUBMIT_NOW,
    CB_CONTENT_TYPE,
    CB_CONTENT_VIEW,
    MktMenuCallback,
    back_to_menu,
    content_card_kb,
    content_list_kb,
    content_new_type_kb,
    content_submit_choice_kb,
    content_types_kb,
)
from bot.api.states.marketing import ContentCreateSG
from bot.api.texts import (
    CONTENT_STATUS_LABELS,
    CONTENT_TYPE_LABELS,
    MKT_CONTENT_ASK_BODY,
    MKT_CONTENT_ASK_MEDIA,
    MKT_CONTENT_ASK_REGION,
    MKT_CONTENT_ASK_SCHEDULED,
    MKT_CONTENT_ASK_TITLE,
    MKT_CONTENT_CARD,
    MKT_CONTENT_CREATED,
    MKT_CONTENT_DATE_INVALID,
    MKT_CONTENT_LIST_EMPTY,
    MKT_CONTENT_LIST_HEADER,
    MKT_CONTENT_NOT_FOUND,
    MKT_CONTENT_PENDING_EMPTY,
    MKT_CONTENT_PENDING_HEADER,
    MKT_CONTENT_PENDING_LINE,
    MKT_CONTENT_PICK_SUBMIT,
    MKT_CONTENT_PICK_TYPE,
    MKT_CONTENT_STATUS_UPDATED,
)
from bot.core.enums import ContentType, SalesMaterialFileType
from bot.db.models.user import User
from bot.services.content_service import ContentService

content_router = Router(name="marketing.content")

DATE_FORMATS = ("%d.%m.%Y %H:%M", "%d.%m.%Y")


def _status_label(value: str) -> str:
    return CONTENT_STATUS_LABELS.get(value, value)


def _type_label(value: str) -> str:
    return CONTENT_TYPE_LABELS.get(value, value)


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
        type_label=_type_label(content_type.value), total=len(items)
    )
    if not items:
        await call.message.answer(
            f"{header}\n\n{MKT_CONTENT_LIST_EMPTY}", reply_markup=back_to_menu()
        )
        return
    lines = [header, ""]
    for item in items:
        lines.append(f"#{item.id} · {_status_label(item.status.value)} · {item.title}")
        if item.region:
            lines.append(f"   📍 {item.region}")
        if item.scheduled_at:
            lines.append(f"   ⏰ {item.scheduled_at:%d.%m.%Y %H:%M}")
        if item.telegram_file_id:
            lines.append(f"   📎 {item.file_type.value if item.file_type else 'media'}")
    await call.message.answer(
        "\n".join(lines), reply_markup=content_list_kb([i.id for i in items])
    )


@content_router.callback_query(F.data == CB_CONTENT_PENDING)
async def list_pending(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    items = await ContentService(session).list_pending()
    if not items:
        await call.message.answer(MKT_CONTENT_PENDING_EMPTY, reply_markup=back_to_menu())
        return
    lines = [MKT_CONTENT_PENDING_HEADER.format(total=len(items)), ""]
    for item in items:
        lines.append(
            MKT_CONTENT_PENDING_LINE.format(
                id=item.id,
                type=_type_label(item.type.value),
                created_at=item.created_at,
                title=item.title,
            )
        )
    await call.message.answer(
        "\n".join(lines), reply_markup=content_list_kb([i.id for i in items])
    )


@content_router.callback_query(F.data.startswith(f"{CB_CONTENT_VIEW}:"))
async def view_card(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    item_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if item_id is None:
        return
    item = await ContentService(session).get(item_id)
    if item is None:
        await call.message.answer(MKT_CONTENT_NOT_FOUND, reply_markup=back_to_menu())
        return
    scheduled = (
        f"{item.scheduled_at:%d.%m.%Y %H:%M}" if item.scheduled_at else "—"
    )
    media_label = (
        f"{item.file_type.value if item.file_type else 'media'}"
        if item.telegram_file_id
        else "—"
    )
    caption = MKT_CONTENT_CARD.format(
        id=item.id,
        type=_type_label(item.type.value),
        status=_status_label(item.status.value),
        region=item.region or "—",
        scheduled_at=scheduled,
        media=media_label,
        title=item.title,
        body=item.body or "—",
    )
    kb = content_card_kb(item.id, item.status.value)
    if item.telegram_file_id and item.file_type is SalesMaterialFileType.PHOTO:
        await call.message.answer_photo(item.telegram_file_id, caption=caption, reply_markup=kb)
    elif item.telegram_file_id and item.file_type is SalesMaterialFileType.VIDEO:
        await call.message.answer_video(item.telegram_file_id, caption=caption, reply_markup=kb)
    elif item.telegram_file_id and item.file_type is SalesMaterialFileType.ANIMATION:
        await call.message.answer_animation(
            item.telegram_file_id, caption=caption, reply_markup=kb
        )
    elif item.telegram_file_id and item.file_type is SalesMaterialFileType.DOCUMENT:
        await call.message.answer_document(item.telegram_file_id, caption=caption, reply_markup=kb)
    else:
        await call.message.answer(caption, reply_markup=kb)


# --- Создание ---


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
async def receive_scheduled(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    scheduled_at: datetime | None = None
    if raw != "-":
        scheduled_at = _parse_date(raw)
        if scheduled_at is None:
            await message.answer(MKT_CONTENT_DATE_INVALID)
            return
    await state.update_data(scheduled_at=scheduled_at.isoformat() if scheduled_at else None)
    await state.set_state(ContentCreateSG.waiting_media)
    await message.answer(MKT_CONTENT_ASK_MEDIA)


@content_router.message(ContentCreateSG.waiting_media)
async def receive_media(message: Message, state: FSMContext) -> None:
    if message.text and message.text.strip() == "-":
        await state.update_data(file_id=None, file_type=None)
    else:
        file_id, file_type = _extract_media(message)
        if file_id is None:
            await message.answer(MKT_CONTENT_ASK_MEDIA)
            return
        await state.update_data(file_id=file_id, file_type=file_type.value)
    await state.set_state(ContentCreateSG.waiting_submit_choice)
    await message.answer(MKT_CONTENT_PICK_SUBMIT, reply_markup=content_submit_choice_kb())


@content_router.callback_query(
    ContentCreateSG.waiting_submit_choice, F.data.startswith(f"{CB_CONTENT_SUBMIT_CHOICE}:")
)
async def finalize(
    call: CallbackQuery, state: FSMContext, app_user: User, session: AsyncSession
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    choice = call.data.rsplit(":", 1)[-1]
    submit = choice == "submit"
    data = await state.get_data()
    scheduled_at = (
        datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None
    )
    file_type = (
        SalesMaterialFileType(data["file_type"]) if data.get("file_type") else None
    )
    service = ContentService(session)
    item = await service.create(
        content_type=ContentType(data["type"]),
        title=data["title"],
        body=data.get("body"),
        region=data.get("region"),
        scheduled_at=scheduled_at,
        author_user_id=app_user.id,
        file_type=file_type,
        telegram_file_id=data.get("file_id"),
        submit_for_approval=submit,
    )
    await state.clear()
    await call.message.answer(
        MKT_CONTENT_CREATED.format(id=item.id, title=item.title)
        + f"\nСтатус: {_status_label(item.status.value)}",
        reply_markup=back_to_menu(),
    )


# --- Смена статуса ---


@content_router.callback_query(F.data.startswith(f"{CB_CONTENT_APPROVE}:"))
async def approve(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await _set_status(call, app_user, session, action="approve")


@content_router.callback_query(F.data.startswith(f"{CB_CONTENT_REJECT}:"))
async def reject(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await _set_status(call, app_user, session, action="reject")


@content_router.callback_query(F.data.startswith(f"{CB_CONTENT_PUBLISH}:"))
async def publish(call: CallbackQuery, session: AsyncSession) -> None:
    await _set_status_simple(call, session, action="publish")


@content_router.callback_query(F.data.startswith(f"{CB_CONTENT_ARCHIVE}:"))
async def archive(call: CallbackQuery, session: AsyncSession) -> None:
    await _set_status_simple(call, session, action="archive")


@content_router.callback_query(F.data.startswith(f"{CB_CONTENT_SUBMIT_NOW}:"))
async def submit_now(call: CallbackQuery, session: AsyncSession) -> None:
    await _set_status_simple(call, session, action="submit")


async def _set_status(
    call: CallbackQuery, app_user: User, session: AsyncSession, *, action: str
) -> None:
    from bot.services.approval_policy import can_approve_marketing

    await call.answer()
    if call.message is None or call.data is None:
        return
    if not await can_approve_marketing(session, app_user):
        await call.message.answer(
            "Одобрение/отклонение доступно только Head of Marketing.",
            reply_markup=back_to_menu(),
        )
        return
    item_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if item_id is None:
        return
    service = ContentService(session)
    if action == "approve":
        item = await service.approve(item_id, approved_by_user_id=app_user.id)
    else:
        item = await service.reject(item_id, approved_by_user_id=app_user.id)
    if item is None:
        await call.message.answer(MKT_CONTENT_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        MKT_CONTENT_STATUS_UPDATED.format(
            id=item.id, status=_status_label(item.status.value)
        ),
        reply_markup=content_card_kb(item.id, item.status.value),
    )


async def _set_status_simple(
    call: CallbackQuery, session: AsyncSession, *, action: str
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    item_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if item_id is None:
        return
    service = ContentService(session)
    if action == "publish":
        item = await service.mark_published(item_id)
    elif action == "archive":
        item = await service.archive(item_id)
    else:
        item = await service.submit_for_approval(item_id)
    if item is None:
        await call.message.answer(MKT_CONTENT_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        MKT_CONTENT_STATUS_UPDATED.format(
            id=item.id, status=_status_label(item.status.value)
        ),
        reply_markup=content_card_kb(item.id, item.status.value),
    )


def _extract_media(message: Message) -> tuple[str | None, SalesMaterialFileType | None]:
    if message.document is not None:
        return message.document.file_id, SalesMaterialFileType.DOCUMENT
    if message.photo:
        return message.photo[-1].file_id, SalesMaterialFileType.PHOTO
    if message.video is not None:
        return message.video.file_id, SalesMaterialFileType.VIDEO
    if message.animation is not None:
        return message.animation.file_id, SalesMaterialFileType.ANIMATION
    return None, None


def _parse_type(raw: str) -> ContentType | None:
    try:
        return ContentType(raw)
    except ValueError:
        return None


def _parse_int(raw: str) -> int | None:
    try:
        return int(raw)
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
