from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import cancel_kb
from bot.api.keyboards.marketing import (
    CB_BROADCAST_CONFIRM,
    CB_BROADCAST_LIST,
    CB_BROADCAST_NEW,
    CB_BROADCAST_SEGMENT,
    MktMenuCallback,
    back_to_menu,
    broadcasts_menu_kb,
    confirm_broadcast_kb,
    segment_kb,
)
from bot.api.states.marketing import BroadcastCreateSG
from bot.api.texts import (
    MKT_BROADCAST_ASK_MEDIA,
    MKT_BROADCAST_ASK_SEGMENT,
    MKT_BROADCAST_ASK_TEXT,
    MKT_BROADCAST_CONFIRM,
    MKT_BROADCAST_FAILED,
    MKT_BROADCAST_LIST_HEADER,
    MKT_BROADCAST_LIST_LINE,
    MKT_BROADCAST_QUEUED,
    MKT_BROADCAST_VALIDATION,
    ROLE_LABELS,
)
from bot.config import Settings
from bot.core.enums import SalesMaterialFileType, UserRole
from bot.core.exceptions import N8nUnavailableError
from bot.db.models.user import User
from bot.db.repositories.broadcast import BroadcastRepository
from bot.db.repositories.user import UserRepository
from bot.services.broadcast_service import BroadcastService
from bot.services.n8n_client import N8nClient

broadcasts_router = Router(name="marketing.broadcasts")


@broadcasts_router.callback_query(F.data == MktMenuCallback.BROADCASTS)
async def show_menu(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.clear()
    await call.message.answer("📣 Рассылки", reply_markup=broadcasts_menu_kb())


@broadcasts_router.callback_query(F.data == CB_BROADCAST_LIST)
async def list_broadcasts(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    broadcasts = await BroadcastRepository(session).list_recent()
    if not broadcasts:
        await call.message.answer("История пуста.", reply_markup=back_to_menu())
        return
    lines = [MKT_BROADCAST_LIST_HEADER]
    for b in broadcasts:
        lines.append(
            MKT_BROADCAST_LIST_LINE.format(
                id=b.id,
                status=b.status.value,
                created_at=b.created_at,
                sent_count=b.sent_count,
            )
        )
    await call.message.answer("\n".join(lines), reply_markup=back_to_menu())


@broadcasts_router.callback_query(F.data == CB_BROADCAST_NEW)
async def start_new(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.set_state(BroadcastCreateSG.waiting_text)
    await call.message.answer(MKT_BROADCAST_ASK_TEXT, reply_markup=cancel_kb())


@broadcasts_router.message(BroadcastCreateSG.waiting_text, F.text)
async def receive_text(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    text_value: str | None = None if raw == "-" else raw
    await state.update_data(text=text_value)
    await state.set_state(BroadcastCreateSG.waiting_media)
    await message.answer(MKT_BROADCAST_ASK_MEDIA)


@broadcasts_router.message(BroadcastCreateSG.waiting_media)
async def receive_media(message: Message, state: FSMContext) -> None:
    if message.text and message.text.strip() == "-":
        await state.update_data(file_id=None, file_type=None)
    else:
        file_id, file_type = _extract_media(message)
        if file_id is None:
            await message.answer(MKT_BROADCAST_ASK_MEDIA)
            return
        await state.update_data(file_id=file_id, file_type=file_type.value)
    data = await state.get_data()
    if not data.get("text") and not data.get("file_id"):
        await message.answer(MKT_BROADCAST_VALIDATION)
        return
    await state.set_state(BroadcastCreateSG.waiting_segment)
    await message.answer(MKT_BROADCAST_ASK_SEGMENT, reply_markup=segment_kb())


@broadcasts_router.callback_query(
    BroadcastCreateSG.waiting_segment, F.data.startswith(f"{CB_BROADCAST_SEGMENT}:")
)
async def pick_segment(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    raw = call.data.rsplit(":", 1)[-1]
    target_role: UserRole | None
    if raw == "all":
        target_role = None
        segment_label = "Все пользователи"
    else:
        try:
            target_role = UserRole(raw)
        except ValueError:
            return
        segment_label = ROLE_LABELS[target_role.value]

    recipients = await UserRepository(session).list_telegram_ids_by_role(target_role)
    data = await state.update_data(
        target_role=target_role.value if target_role else None,
        recipients_count=len(recipients),
    )
    await state.set_state(BroadcastCreateSG.waiting_confirm)
    await call.message.answer(
        MKT_BROADCAST_CONFIRM.format(
            segment=segment_label,
            recipients=len(recipients),
            media="есть" if data.get("file_id") else "нет",
            text=data.get("text") or "—",
        ),
        reply_markup=confirm_broadcast_kb(),
    )


@broadcasts_router.callback_query(
    BroadcastCreateSG.waiting_confirm, F.data == f"{CB_BROADCAST_CONFIRM}:no"
)
async def cancel_confirm(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await state.clear()
    if call.message is not None:
        await call.message.answer("Рассылка отменена.", reply_markup=back_to_menu())


@broadcasts_router.callback_query(
    BroadcastCreateSG.waiting_confirm, F.data == f"{CB_BROADCAST_CONFIRM}:yes"
)
async def confirm_send(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    app_user: User,
    http_client: AsyncClient,
    settings: Settings,
) -> None:
    await call.answer()
    if call.message is None:
        return
    data = await state.get_data()
    target_role = UserRole(data["target_role"]) if data.get("target_role") else None
    file_type = SalesMaterialFileType(data["file_type"]) if data.get("file_type") else None

    n8n = N8nClient(settings.n8n, http_client)
    service = BroadcastService(session, n8n)
    broadcast = await service.create_draft(
        text=data.get("text"),
        file_type=file_type,
        telegram_file_id=data.get("file_id"),
        target_role=target_role,
        created_by_user_id=app_user.id,
    )
    try:
        broadcast = await service.send(broadcast)
    except N8nUnavailableError as exc:
        await state.clear()
        await call.message.answer(
            MKT_BROADCAST_FAILED.format(error=str(exc)), reply_markup=back_to_menu()
        )
        return

    await state.clear()
    await call.message.answer(
        MKT_BROADCAST_QUEUED.format(id=broadcast.id, count=broadcast.sent_count),
        reply_markup=back_to_menu(),
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


