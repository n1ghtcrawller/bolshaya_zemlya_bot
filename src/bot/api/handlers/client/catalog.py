from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.catalog import (
    CB_BACK_TO_CATEGORIES,
    CB_CATEGORY,
    CB_PRODUCT,
    CB_PRODUCT_PAGE,
    CB_PRODUCT_REQUEST,
    categories_kb,
    product_card_kb,
    products_page_kb,
)
from bot.api.keyboards.client import ClientMenuCallback, back_to_menu, cancel_kb
from bot.api.states.client import CreateRequestSG
from bot.api.texts import (
    CATALOG_CATEGORY_EMPTY,
    CATALOG_CATEGORY_HEADER,
    CATALOG_EMPTY,
    CATALOG_HEADER,
    CATALOG_PICKER_HEADER,
    CATALOG_PRODUCT_NOT_FOUND,
    CATALOG_PRODUCT_TEMPLATE,
    CATALOG_REQUEST_NOTE_PREFIX,
    REQUEST_ASK_NAME,
)
from bot.db.models.user import User
from bot.services.catalog_service import CatalogService

catalog_router = Router(name="client.catalog")

BACK_CB = "client:back_to_menu"


@catalog_router.callback_query(F.data == ClientMenuCallback.CATALOG)
async def show_catalog(call: CallbackQuery, session: AsyncSession) -> None:
    await _show_categories(call, session, header=CATALOG_HEADER)


@catalog_router.callback_query(F.data == ClientMenuCallback.PICKER)
async def show_picker(call: CallbackQuery, session: AsyncSession) -> None:
    await _show_categories(call, session, header=CATALOG_PICKER_HEADER)


@catalog_router.callback_query(F.data == CB_BACK_TO_CATEGORIES)
async def back_to_categories(call: CallbackQuery, session: AsyncSession) -> None:
    await _show_categories(call, session, header=CATALOG_HEADER)


@catalog_router.callback_query(F.data.startswith(f"{CB_CATEGORY}:"))
async def show_category(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        category_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    await _render_category_page(call, session, category_id, page=0)


@catalog_router.callback_query(F.data.startswith(f"{CB_PRODUCT_PAGE}:"))
async def paginate_category(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    parts = call.data.split(":")
    if len(parts) != 4:
        return
    try:
        category_id = int(parts[-2])
        page = int(parts[-1])
    except ValueError:
        return
    await _render_category_page(call, session, category_id, page=page)


@catalog_router.callback_query(F.data.startswith(f"{CB_PRODUCT}:"))
async def show_product(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        product_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    service = CatalogService(session)
    product = await service.get_product(product_id)
    if product is None:
        await call.message.answer(CATALOG_PRODUCT_NOT_FOUND, reply_markup=back_to_menu())
        return
    caption = CATALOG_PRODUCT_TEMPLATE.format(
        name=product.name,
        category=product.category.name,
        price=product.price_text or "по запросу",
        short=product.short_description or "",
        full=product.full_description or "",
        specs=product.specs or "—",
    )
    keyboard = product_card_kb(product.id, product.category_id, back_callback=BACK_CB)
    if product.main_photo_file_id:
        await call.message.answer_photo(
            product.main_photo_file_id, caption=caption, reply_markup=keyboard
        )
    else:
        await call.message.answer(caption, reply_markup=keyboard)


@catalog_router.callback_query(F.data.startswith(f"{CB_PRODUCT_REQUEST}:"))
async def start_product_request(
    call: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    app_user: User,
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        product_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    service = CatalogService(session)
    product = await service.get_product(product_id)
    if product is None:
        await call.message.answer(CATALOG_PRODUCT_NOT_FOUND, reply_markup=back_to_menu())
        return
    note = CATALOG_REQUEST_NOTE_PREFIX.format(name=product.name, id=product.id)
    await state.set_state(CreateRequestSG.name)
    await state.update_data(
        prefill_name=app_user.full_name,
        comment_prefix=note,
        product_id=product.id,
    )
    await call.message.answer(REQUEST_ASK_NAME, reply_markup=cancel_kb())


async def _show_categories(call: CallbackQuery, session: AsyncSession, *, header: str) -> None:
    await call.answer()
    if call.message is None:
        return
    service = CatalogService(session)
    categories = await service.list_categories()
    if not categories:
        await call.message.answer(CATALOG_EMPTY, reply_markup=back_to_menu())
        return
    await call.message.answer(
        header,
        reply_markup=categories_kb(
            [(c.id, c.name) for c in categories], back_callback=BACK_CB
        ),
    )


async def _render_category_page(
    call: CallbackQuery,
    session: AsyncSession,
    category_id: int,
    *,
    page: int,
) -> None:
    if call.message is None:
        return
    service = CatalogService(session)
    category = await service.get_category(category_id)
    if category is None:
        await call.message.answer(CATALOG_EMPTY, reply_markup=back_to_menu())
        return
    items, page, pages = await service.page(category_id, page)
    if not items:
        await call.message.answer(
            f"{category.name}\n\n{CATALOG_CATEGORY_EMPTY}", reply_markup=back_to_menu()
        )
        return
    lines = [CATALOG_CATEGORY_HEADER.format(name=category.name, total=len(items)), ""]
    for item in items:
        lines.append(f"📦 <b>#{item.id} {item.name}</b>")
        if item.short_description:
            lines.append(item.short_description)
        if item.price_text:
            lines.append(f"💰 {item.price_text}")
        lines.append("")
    await call.message.answer(
        "\n".join(lines).rstrip(),
        reply_markup=products_page_kb(
            category_id, page, pages, [i.id for i in items], back_callback=BACK_CB
        ),
    )
