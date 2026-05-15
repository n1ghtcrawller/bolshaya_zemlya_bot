from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.marketing import (
    CB_MOD_APPROVE,
    CB_MOD_REJECT,
    CB_MOD_VIEW,
    MktMenuCallback,
    back_to_menu,
    moderation_actions_kb,
    moderation_list_kb,
)
from bot.api.texts import (
    MATERIAL_CATEGORY_LABELS,
    MKT_MODERATION_APPROVED,
    MKT_MODERATION_DETAILS,
    MKT_MODERATION_EMPTY,
    MKT_MODERATION_ITEM_LINE,
    MKT_MODERATION_LIST_HEADER,
    MKT_MODERATION_NOT_FOUND,
    MKT_MODERATION_REJECTED,
)
from bot.core.enums import SalesMaterialFileType
from bot.db.models.user import User
from bot.services.material_moderation_service import MaterialModerationService

moderation_router = Router(name="marketing.moderation")


@moderation_router.callback_query(F.data == MktMenuCallback.MODERATION)
async def list_pending(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None:
        return
    items = await MaterialModerationService(session).list_pending()
    if not items:
        await call.message.answer(MKT_MODERATION_EMPTY, reply_markup=back_to_menu())
        return
    lines = [MKT_MODERATION_LIST_HEADER.format(total=len(items)), ""]
    for m in items:
        lines.append(
            MKT_MODERATION_ITEM_LINE.format(
                id=m.id,
                category=MATERIAL_CATEGORY_LABELS.get(m.category.value, m.category.value),
                file_type=m.file_type.value,
                author_id=m.uploaded_by_user_id or "—",
                title=m.title,
            )
        )
    await call.message.answer(
        "\n".join(lines), reply_markup=moderation_list_kb([m.id for m in items])
    )


@moderation_router.callback_query(F.data.startswith(f"{CB_MOD_VIEW}:"))
async def view(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        material_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    material = await MaterialModerationService(session).get(material_id)
    if material is None:
        await call.message.answer(MKT_MODERATION_NOT_FOUND, reply_markup=back_to_menu())
        return

    caption = MKT_MODERATION_DETAILS.format(
        id=material.id,
        category=MATERIAL_CATEGORY_LABELS.get(material.category.value, material.category.value),
        file_type=material.file_type.value,
        author_id=material.uploaded_by_user_id or "—",
        title=material.title,
        description=material.description or "—",
    )
    kb = moderation_actions_kb(material.id)
    file_id = material.telegram_file_id
    if material.file_type is SalesMaterialFileType.PHOTO:
        await call.message.answer_photo(file_id, caption=caption, reply_markup=kb)
    elif material.file_type is SalesMaterialFileType.VIDEO:
        await call.message.answer_video(file_id, caption=caption, reply_markup=kb)
    elif material.file_type is SalesMaterialFileType.ANIMATION:
        await call.message.answer_animation(file_id, caption=caption, reply_markup=kb)
    else:
        await call.message.answer_document(file_id, caption=caption, reply_markup=kb)


@moderation_router.callback_query(F.data.startswith(f"{CB_MOD_APPROVE}:"))
async def approve(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        material_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    material = await MaterialModerationService(session).approve(
        material_id, approved_by_user_id=app_user.id
    )
    if material is None:
        await call.message.answer(MKT_MODERATION_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        MKT_MODERATION_APPROVED.format(id=material.id), reply_markup=back_to_menu()
    )


@moderation_router.callback_query(F.data.startswith(f"{CB_MOD_REJECT}:"))
async def reject(call: CallbackQuery, app_user: User, session: AsyncSession) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        material_id = int(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    material = await MaterialModerationService(session).reject(
        material_id, approved_by_user_id=app_user.id
    )
    if material is None:
        await call.message.answer(MKT_MODERATION_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        MKT_MODERATION_REJECTED.format(id=material.id), reply_markup=back_to_menu()
    )
