from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.sales import (
    CB_DIRECTORY_REGION,
    SalesMenuCallback,
    back_to_menu,
    dealers_kb,
    region_token,
    regions_kb,
)
from bot.api.texts import (
    SALES_FIND_DEALER_HEADER,
    SALES_FIND_DEALER_NO_REGIONS,
)
from bot.services.dealer_directory_service import DealerDirectoryService

find_dealer_router = Router(name="sales.find_dealer")


@find_dealer_router.callback_query(F.data == SalesMenuCallback.FIND_DEALER)
async def show_regions(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    directory = DealerDirectoryService(session)
    regions = await directory.list_regions()
    if not regions:
        await call.message.answer(SALES_FIND_DEALER_NO_REGIONS, reply_markup=back_to_menu())
        return
    await call.message.answer(
        SALES_FIND_DEALER_HEADER,
        reply_markup=regions_kb(list(regions), callback_prefix=CB_DIRECTORY_REGION),
    )


@find_dealer_router.callback_query(F.data.startswith(f"{CB_DIRECTORY_REGION}:"))
async def show_region_dealers(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    token = call.data.rsplit(":", 1)[-1]
    directory = DealerDirectoryService(session)
    regions = await directory.list_regions()
    region = next((r for r in regions if region_token(r) == token), None)
    if region is None:
        await call.message.answer(SALES_FIND_DEALER_NO_REGIONS, reply_markup=back_to_menu())
        return
    dealers = await directory.list_by_region(region)
    if not dealers:
        await call.message.answer(
            f"📍 {region}\n\nВ этом регионе пока нет активных дилеров.",
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
        f"📍 {region} — выберите диллера:",
        reply_markup=dealers_kb(options, lead_id=None),
    )
