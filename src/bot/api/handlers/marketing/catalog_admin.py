from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import cancel_kb
from bot.api.keyboards.marketing import (
    CB_CATALOG_NEW_CATEGORY,
    CB_CATALOG_NEW_PRODUCT,
    CB_CATALOG_PICK_CATEGORY,
    MktMenuCallback,
    back_to_menu,
    catalog_admin_menu_kb,
    catalog_pick_category_kb,
)
from bot.api.states.marketing import CatalogCategoryCreateSG, CatalogProductCreateSG
from bot.api.texts import (
    MKT_CATALOG_CATEGORY_CREATED,
    MKT_CATALOG_HEADER,
    MKT_CATALOG_NEW_CATEGORY,
    MKT_CATALOG_NO_CATEGORIES,
    MKT_CATALOG_PICK_CATEGORY_FOR_PRODUCT,
    MKT_CATALOG_PRODUCT_ASK_FULL,
    MKT_CATALOG_PRODUCT_ASK_NAME,
    MKT_CATALOG_PRODUCT_ASK_PHOTO,
    MKT_CATALOG_PRODUCT_ASK_PRICE,
    MKT_CATALOG_PRODUCT_ASK_SHORT,
    MKT_CATALOG_PRODUCT_ASK_SPECS,
    MKT_CATALOG_PRODUCT_CREATED,
)
from bot.db.models.user import User
from bot.services.catalog_admin_service import CatalogAdminService
from bot.services.catalog_service import CatalogService

catalog_admin_router = Router(name="marketing.catalog_admin")


@catalog_admin_router.callback_query(F.data == MktMenuCallback.CATALOG)
async def show_admin_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.clear()
    categories = await CatalogService(session).list_categories()
    await call.message.answer(
        MKT_CATALOG_HEADER.format(categories_total=len(categories)),
        reply_markup=catalog_admin_menu_kb(),
    )


# --- Создание категории ---


@catalog_admin_router.callback_query(F.data == CB_CATALOG_NEW_CATEGORY)
async def new_category_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.set_state(CatalogCategoryCreateSG.waiting_name)
    await call.message.answer(MKT_CATALOG_NEW_CATEGORY, reply_markup=cancel_kb())


@catalog_admin_router.message(CatalogCategoryCreateSG.waiting_name, F.text)
async def new_category_save(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(MKT_CATALOG_NEW_CATEGORY)
        return
    category = await CatalogAdminService(session).create_category(name=name)
    await state.clear()
    await message.answer(
        MKT_CATALOG_CATEGORY_CREATED.format(name=category.name, id=category.id),
        reply_markup=catalog_admin_menu_kb(),
    )


# --- Создание товара ---


@catalog_admin_router.callback_query(F.data == CB_CATALOG_NEW_PRODUCT)
async def new_product_pick_category(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await call.answer()
    if call.message is None:
        return
    categories = await CatalogService(session).list_categories()
    if not categories:
        await call.message.answer(MKT_CATALOG_NO_CATEGORIES, reply_markup=catalog_admin_menu_kb())
        return
    await call.message.answer(
        MKT_CATALOG_PICK_CATEGORY_FOR_PRODUCT,
        reply_markup=catalog_pick_category_kb([(c.id, c.name) for c in categories]),
    )


@catalog_admin_router.callback_query(F.data.startswith(f"{CB_CATALOG_PICK_CATEGORY}:"))
async def new_product_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        category_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    await state.set_state(CatalogProductCreateSG.waiting_name)
    await state.update_data(category_id=category_id)
    await call.message.answer(MKT_CATALOG_PRODUCT_ASK_NAME, reply_markup=cancel_kb())


@catalog_admin_router.message(CatalogProductCreateSG.waiting_name, F.text)
async def product_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(MKT_CATALOG_PRODUCT_ASK_NAME)
        return
    await state.update_data(name=name)
    await state.set_state(CatalogProductCreateSG.waiting_short)
    await message.answer(MKT_CATALOG_PRODUCT_ASK_SHORT)


@catalog_admin_router.message(CatalogProductCreateSG.waiting_short, F.text)
async def product_short(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    await state.update_data(short_description=None if raw == "-" else raw)
    await state.set_state(CatalogProductCreateSG.waiting_full)
    await message.answer(MKT_CATALOG_PRODUCT_ASK_FULL)


@catalog_admin_router.message(CatalogProductCreateSG.waiting_full, F.text)
async def product_full(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    await state.update_data(full_description=None if raw == "-" else raw)
    await state.set_state(CatalogProductCreateSG.waiting_price)
    await message.answer(MKT_CATALOG_PRODUCT_ASK_PRICE)


@catalog_admin_router.message(CatalogProductCreateSG.waiting_price, F.text)
async def product_price(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    await state.update_data(price_text=None if raw == "-" else raw)
    await state.set_state(CatalogProductCreateSG.waiting_specs)
    await message.answer(MKT_CATALOG_PRODUCT_ASK_SPECS)


@catalog_admin_router.message(CatalogProductCreateSG.waiting_specs, F.text)
async def product_specs(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    await state.update_data(specs=None if raw == "-" else raw)
    await state.set_state(CatalogProductCreateSG.waiting_photo)
    await message.answer(MKT_CATALOG_PRODUCT_ASK_PHOTO)


@catalog_admin_router.message(CatalogProductCreateSG.waiting_photo)
async def product_photo(
    message: Message, state: FSMContext, session: AsyncSession, app_user: User
) -> None:
    if message.text and message.text.strip() == "-":
        photo_file_id: str | None = None
    elif message.photo:
        photo_file_id = message.photo[-1].file_id
    else:
        await message.answer(MKT_CATALOG_PRODUCT_ASK_PHOTO)
        return

    data = await state.get_data()
    service = CatalogAdminService(session)
    product = await service.create_product(
        category_id=int(data["category_id"]),
        name=data["name"],
        short_description=data.get("short_description"),
        full_description=data.get("full_description"),
        price_text=data.get("price_text"),
        specs=data.get("specs"),
        main_photo_file_id=photo_file_id,
        created_by_user_id=app_user.id,
    )
    await state.clear()
    category_name = product.category.name if product.category else "—"
    await message.answer(
        MKT_CATALOG_PRODUCT_CREATED.format(
            id=product.id, name=product.name, category=category_name
        ),
        reply_markup=back_to_menu(),
    )
