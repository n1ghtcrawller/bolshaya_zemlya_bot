from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.dealer import (
    CB_MATERIAL_CATEGORY,
    CB_MATERIAL_PAGE,
    CB_MATERIAL_SEND,
    DealerMenuCallback,
    back_to_menu,
    materials_categories_with_submit_kb,
    materials_page_kb,
)
from bot.api.texts import (
    DEALER_MATERIAL_NOT_FOUND,
    DEALER_MATERIALS_EMPTY,
    DEALER_MATERIALS_HEADER,
    MATERIAL_CATEGORY_LABELS,
)
from bot.core.enums import SalesMaterialCategory, SalesMaterialFileType
from bot.services.sales_material_service import SalesMaterialService

materials_router = Router(name="dealer.materials")


@materials_router.callback_query(F.data == DealerMenuCallback.MATERIALS)
async def show_categories(call: CallbackQuery) -> None:
    await call.answer()
    if call.message is None:
        return
    await call.message.answer(DEALER_MATERIALS_HEADER, reply_markup=materials_categories_with_submit_kb())


@materials_router.callback_query(F.data.startswith(f"{CB_MATERIAL_CATEGORY}:"))
async def show_category_page(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    raw_cat = call.data.rsplit(":", 1)[-1]
    category = _parse_category(raw_cat)
    if category is None:
        return
    await _render_page(call, session, category, page=0)


@materials_router.callback_query(F.data.startswith(f"{CB_MATERIAL_PAGE}:"))
async def paginate(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    parts = call.data.split(":")
    if len(parts) != 5:
        return
    _, _, _, raw_cat, raw_page = parts
    category = _parse_category(raw_cat)
    if category is None:
        return
    try:
        page = int(raw_page)
    except ValueError:
        return
    await _render_page(call, session, category, page=page)


@materials_router.callback_query(F.data.startswith(f"{CB_MATERIAL_SEND}:"))
async def send_material(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        material_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    service = SalesMaterialService(session)
    material = await service.get(material_id)
    if material is None or not material.is_active:
        await call.message.answer(DEALER_MATERIAL_NOT_FOUND, reply_markup=back_to_menu())
        return

    caption = f"<b>{material.title}</b>"
    if material.description:
        caption = f"{caption}\n\n{material.description}"

    if material.file_type is SalesMaterialFileType.PHOTO:
        await call.message.answer_photo(material.telegram_file_id, caption=caption)
    elif material.file_type is SalesMaterialFileType.VIDEO:
        await call.message.answer_video(material.telegram_file_id, caption=caption)
    elif material.file_type is SalesMaterialFileType.ANIMATION:
        await call.message.answer_animation(material.telegram_file_id, caption=caption)
    else:
        await call.message.answer_document(material.telegram_file_id, caption=caption)


async def _render_page(
    call: CallbackQuery,
    session: AsyncSession,
    category: SalesMaterialCategory,
    *,
    page: int,
) -> None:
    if call.message is None:
        return
    service = SalesMaterialService(session)
    items, page, pages = await service.get_page(category, page)
    label = MATERIAL_CATEGORY_LABELS.get(category.value, category.value)
    if not items:
        await call.message.answer(
            f"{label}\n\n{DEALER_MATERIALS_EMPTY}",
            reply_markup=materials_categories_with_submit_kb(),
        )
        return
    lines = [label, ""]
    for item in items:
        lines.append(f"📎 <b>#{item.id} {item.title}</b>")
        if item.description:
            lines.append(item.description)
        lines.append("")
    await call.message.answer(
        "\n".join(lines).rstrip(),
        reply_markup=materials_page_kb(
            category, page, pages, [(m.id, m.title) for m in items]
        ),
    )


def _parse_category(raw: str) -> SalesMaterialCategory | None:
    try:
        return SalesMaterialCategory(raw)
    except ValueError:
        return None
