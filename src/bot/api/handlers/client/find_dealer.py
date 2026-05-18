from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import (
    CB_DEALER_CALLBACK,
    CB_DEALER_REQUEST,
    CB_FIND_DEALER,
    CB_FIND_REGION,
    ClientMenuCallback,
    back_to_menu,
    cancel_kb,
    find_dealer_card_kb,
    find_dealer_list_kb,
    find_dealer_regions_kb,
    share_contact_kb,
)
from bot.api.keyboards.sales import dealer_tg_url, region_token
from bot.api.states.client import CallbackSG, CreateRequestSG
from bot.api.texts import (
    CLIENT_CALLBACK_ASK_PHONE,
    CLIENT_CALLBACK_INTRO,
    CLIENT_DEALER_CARD,
    CLIENT_DEALER_NOT_FOUND,
    CLIENT_DEALER_REQUEST_NOTE,
    CLIENT_FIND_DEALER_HEADER,
    CLIENT_FIND_DEALER_NO_REGIONS,
    CLIENT_FIND_DEALER_REGION_EMPTY,
    CLIENT_FIND_DEALER_REGION_HEADER,
    REQUEST_ASK_NAME,
)
from bot.db.models.user import User
from bot.services.dealer_directory_service import DealerDirectoryService

find_dealer_router = Router(name="client.find_dealer")


@find_dealer_router.callback_query(F.data == ClientMenuCallback.FIND_DEALER)
async def show_regions(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    directory = DealerDirectoryService(session)
    regions = await directory.list_regions()
    if not regions:
        await call.message.answer(
            CLIENT_FIND_DEALER_NO_REGIONS, reply_markup=back_to_menu()
        )
        return
    tokens = [(r, region_token(r)) for r in regions]
    await call.message.answer(
        CLIENT_FIND_DEALER_HEADER, reply_markup=find_dealer_regions_kb(tokens)
    )


@find_dealer_router.callback_query(F.data.startswith(f"{CB_FIND_REGION}:"))
async def show_dealers(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    token = call.data.rsplit(":", 1)[-1]
    directory = DealerDirectoryService(session)
    regions = await directory.list_regions()
    region = next((r for r in regions if region_token(r) == token), None)
    if region is None:
        await call.message.answer(
            CLIENT_FIND_DEALER_NO_REGIONS, reply_markup=back_to_menu()
        )
        return
    dealers = await directory.list_by_region(region)
    if not dealers:
        await call.message.answer(
            f"📍 {region}\n\n{CLIENT_FIND_DEALER_REGION_EMPTY}",
            reply_markup=back_to_menu(),
        )
        return
    options: list[tuple[int, str]] = []
    for user, profile in dealers:
        label = user.full_name
        if profile and profile.company:
            label = f"{user.full_name} · {profile.company}"
        options.append((user.id, label))
    await call.message.answer(
        CLIENT_FIND_DEALER_REGION_HEADER.format(region=region),
        reply_markup=find_dealer_list_kb(options),
    )


@find_dealer_router.callback_query(F.data.startswith(f"{CB_FIND_DEALER}:"))
async def show_dealer_card(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    dealer_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if dealer_id is None:
        return
    directory = DealerDirectoryService(session)
    dealer = await directory.get_dealer(dealer_id)
    if dealer is None:
        await call.message.answer(CLIENT_DEALER_NOT_FOUND, reply_markup=back_to_menu())
        return
    user, profile = dealer
    text = CLIENT_DEALER_CARD.format(
        full_name=user.full_name,
        company=(profile.company if profile else None) or "—",
        region=(profile.region if profile else None) or "—",
        address=(profile.address if profile else None) or "—",
        phone=(profile.phone if profile else None) or "—",
        specialization=(profile.specialization if profile else None) or "—",
        description=(profile.description if profile else None) or "—",
    )
    keyboard = find_dealer_card_kb(
        dealer_id=user.id,
        tg_url=dealer_tg_url(username=user.username, telegram_id=user.telegram_id),
    )
    await call.message.answer(text, reply_markup=keyboard)


@find_dealer_router.callback_query(F.data.startswith(f"{CB_DEALER_REQUEST}:"))
async def start_request_for_dealer(
    call: CallbackQuery, state: FSMContext, app_user: User, session: AsyncSession
) -> None:
    """Запускает существующий FSM CreateRequestSG, подставляя пометку о диллере."""
    await call.answer()
    if call.message is None or call.data is None:
        return
    dealer_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if dealer_id is None:
        return
    directory = DealerDirectoryService(session)
    dealer = await directory.get_dealer(dealer_id)
    if dealer is None:
        await call.message.answer(CLIENT_DEALER_NOT_FOUND, reply_markup=back_to_menu())
        return
    user, _ = dealer
    note = CLIENT_DEALER_REQUEST_NOTE.format(full_name=user.full_name, dealer_id=user.id)
    await state.set_state(CreateRequestSG.name)
    await state.update_data(prefill_name=app_user.full_name, comment_prefix=note)
    await call.message.answer(REQUEST_ASK_NAME, reply_markup=cancel_kb())


@find_dealer_router.callback_query(F.data.startswith(f"{CB_DEALER_CALLBACK}:"))
async def start_callback_for_dealer(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Запускает существующий FSM CallbackSG с пометкой о диллере."""
    await call.answer()
    if call.message is None or call.data is None:
        return
    dealer_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if dealer_id is None:
        return
    directory = DealerDirectoryService(session)
    dealer = await directory.get_dealer(dealer_id)
    if dealer is None:
        await call.message.answer(CLIENT_DEALER_NOT_FOUND, reply_markup=back_to_menu())
        return
    user, _ = dealer
    note = CLIENT_DEALER_REQUEST_NOTE.format(full_name=user.full_name, dealer_id=user.id)
    await state.set_state(CallbackSG.waiting_phone)
    await state.update_data(comment_prefix=note)
    await call.message.answer(CLIENT_CALLBACK_INTRO)
    await call.message.answer(CLIENT_CALLBACK_ASK_PHONE, reply_markup=share_contact_kb())


def _parse_int(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None
