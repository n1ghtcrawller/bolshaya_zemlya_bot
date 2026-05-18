from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import cancel_kb
from bot.api.keyboards.marketing import (
    CB_EXPO_LIST,
    CB_EXPO_NEW,
    CB_EXPO_VIEW,
    MktMenuCallback,
    back_to_menu,
    expos_list_kb,
    expos_menu_kb,
)
from bot.api.states.marketing import ExpoCreateSG
from bot.api.texts import (
    MKT_EXPO_ASK_DESCRIPTION,
    MKT_EXPO_ASK_ENDS,
    MKT_EXPO_ASK_LOCATION,
    MKT_EXPO_ASK_PRODUCTS,
    MKT_EXPO_ASK_STARTS,
    MKT_EXPO_ASK_TITLE,
    MKT_EXPO_CREATED,
    MKT_EXPO_DETAILS,
    MKT_EXPO_LIST_EMPTY,
    MKT_EXPO_LIST_HEADER,
    MKT_EXPO_LIST_LINE,
)
from bot.db.models.user import User
from bot.services.expo_service import ExpoService

expos_router = Router(name="marketing.expos")

DATE_FORMAT = "%d.%m.%Y"


@expos_router.callback_query(F.data == MktMenuCallback.EXPOS)
async def show_menu(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.clear()
    await call.message.answer("🎪 Выставки", reply_markup=expos_menu_kb())


@expos_router.callback_query(F.data == CB_EXPO_LIST)
async def list_upcoming(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    items = await ExpoService(session).list_upcoming()
    if not items:
        await call.message.answer(MKT_EXPO_LIST_EMPTY, reply_markup=back_to_menu())
        return
    lines = [MKT_EXPO_LIST_HEADER]
    for expo in items:
        lines.append(
            MKT_EXPO_LIST_LINE.format(id=expo.id, starts_at=expo.starts_at, title=expo.title)
        )
    button_items = [(e.id, f"{e.starts_at:%d.%m} · {e.title}") for e in items]
    await call.message.answer(
        "\n".join(lines), reply_markup=expos_list_kb(button_items)
    )


@expos_router.callback_query(F.data.startswith(f"{CB_EXPO_VIEW}:"))
async def view_expo(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        expo_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    expo = await ExpoService(session).get(expo_id)
    if expo is None:
        await call.message.answer("Выставка не найдена.", reply_markup=back_to_menu())
        return
    dates = f"{expo.starts_at:%d.%m.%Y}"
    if expo.ends_at:
        dates = f"{dates} — {expo.ends_at:%d.%m.%Y}"
    await call.message.answer(
        MKT_EXPO_DETAILS.format(
            id=expo.id,
            title=expo.title,
            location=expo.location or "—",
            dates=dates,
            products=expo.products or "—",
            description=expo.description or "—",
        ),
        reply_markup=back_to_menu(),
    )


@expos_router.callback_query(F.data == CB_EXPO_NEW)
async def start_new(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.set_state(ExpoCreateSG.waiting_title)
    await call.message.answer(MKT_EXPO_ASK_TITLE, reply_markup=cancel_kb())


@expos_router.message(ExpoCreateSG.waiting_title, F.text)
async def receive_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer(MKT_EXPO_ASK_TITLE)
        return
    await state.update_data(title=title)
    await state.set_state(ExpoCreateSG.waiting_location)
    await message.answer(MKT_EXPO_ASK_LOCATION)


@expos_router.message(ExpoCreateSG.waiting_location, F.text)
async def receive_location(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    await state.update_data(location=None if raw == "-" else raw)
    await state.set_state(ExpoCreateSG.waiting_starts)
    await message.answer(MKT_EXPO_ASK_STARTS)


@expos_router.message(ExpoCreateSG.waiting_starts, F.text)
async def receive_starts(message: Message, state: FSMContext) -> None:
    starts = _parse_date(message.text or "")
    if starts is None:
        await message.answer(MKT_EXPO_ASK_STARTS)
        return
    await state.update_data(starts_at=starts.isoformat())
    await state.set_state(ExpoCreateSG.waiting_ends)
    await message.answer(MKT_EXPO_ASK_ENDS)


@expos_router.message(ExpoCreateSG.waiting_ends, F.text)
async def receive_ends(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    ends_at: datetime | None = None
    if raw != "-":
        ends_at = _parse_date(raw)
        if ends_at is None:
            await message.answer(MKT_EXPO_ASK_ENDS)
            return
    await state.update_data(ends_at=ends_at.isoformat() if ends_at else None)
    await state.set_state(ExpoCreateSG.waiting_products)
    await message.answer(MKT_EXPO_ASK_PRODUCTS)


@expos_router.message(ExpoCreateSG.waiting_products, F.text)
async def receive_products(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    await state.update_data(products=None if raw == "-" else raw)
    await state.set_state(ExpoCreateSG.waiting_description)
    await message.answer(MKT_EXPO_ASK_DESCRIPTION)


@expos_router.message(ExpoCreateSG.waiting_description, F.text)
async def receive_description(
    message: Message, state: FSMContext, app_user: User, session: AsyncSession
) -> None:
    raw = (message.text or "").strip()
    description = None if raw == "-" else raw
    data = await state.get_data()
    starts_at = datetime.fromisoformat(data["starts_at"])
    ends_at = datetime.fromisoformat(data["ends_at"]) if data.get("ends_at") else None
    expo = await ExpoService(session).create(
        title=data["title"],
        location=data.get("location"),
        description=description,
        products=data.get("products"),
        starts_at=starts_at,
        ends_at=ends_at,
        created_by_user_id=app_user.id,
    )
    await state.clear()
    await message.answer(
        MKT_EXPO_CREATED.format(id=expo.id, title=expo.title),
        reply_markup=back_to_menu(),
    )


def _parse_date(raw: str) -> datetime | None:
    raw = raw.strip()
    try:
        naive = datetime.strptime(raw, DATE_FORMAT)
    except ValueError:
        return None
    return naive.replace(tzinfo=timezone.utc)
