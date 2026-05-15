from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.client import cancel_kb
from bot.api.keyboards.marketing import (
    CB_MATERIAL_CATEGORY,
    MktMenuCallback,
    back_to_menu,
    material_categories_kb,
)
from bot.api.states.marketing import MaterialUploadSG
from bot.api.texts import (
    MATERIAL_CATEGORY_LABELS,
    MKT_MATERIALS_ASK_DESCRIPTION,
    MKT_MATERIALS_ASK_FILE,
    MKT_MATERIALS_ASK_TITLE,
    MKT_MATERIALS_CREATED,
    MKT_MATERIALS_PICK_CATEGORY,
)
from bot.core.enums import SalesMaterialCategory, SalesMaterialFileType
from bot.db.models.user import User
from bot.services.material_upload_service import MaterialUploadService

materials_router = Router(name="marketing.materials_upload")


@materials_router.callback_query(F.data == MktMenuCallback.MATERIALS)
async def pick_category(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None:
        return
    await state.clear()
    await call.message.answer(
        MKT_MATERIALS_PICK_CATEGORY, reply_markup=material_categories_kb()
    )


@materials_router.callback_query(F.data.startswith(f"{CB_MATERIAL_CATEGORY}:"))
async def start_upload(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    try:
        category = SalesMaterialCategory(call.data.rsplit(":", 1)[-1])
    except ValueError:
        return
    await state.set_state(MaterialUploadSG.waiting_file)
    await state.update_data(category=category.value)
    await call.message.answer(MKT_MATERIALS_ASK_FILE, reply_markup=cancel_kb())


@materials_router.message(MaterialUploadSG.waiting_file)
async def receive_file(message: Message, state: FSMContext) -> None:
    file_id, file_type = _extract_media(message)
    if file_id is None or file_type is None:
        await message.answer(MKT_MATERIALS_ASK_FILE)
        return
    await state.update_data(file_id=file_id, file_type=file_type.value)
    await state.set_state(MaterialUploadSG.waiting_title)
    await message.answer(MKT_MATERIALS_ASK_TITLE)


@materials_router.message(MaterialUploadSG.waiting_title, F.text)
async def receive_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer(MKT_MATERIALS_ASK_TITLE)
        return
    await state.update_data(title=title)
    await state.set_state(MaterialUploadSG.waiting_description)
    await message.answer(MKT_MATERIALS_ASK_DESCRIPTION)


@materials_router.message(MaterialUploadSG.waiting_description, F.text)
async def receive_description(
    message: Message, state: FSMContext, app_user: User, session: AsyncSession
) -> None:
    raw = (message.text or "").strip()
    description = None if raw == "-" else raw
    data = await state.get_data()
    service = MaterialUploadService(session)
    material = await service.upload(
        category=SalesMaterialCategory(data["category"]),
        title=data["title"],
        description=description,
        file_type=SalesMaterialFileType(data["file_type"]),
        telegram_file_id=data["file_id"],
        uploaded_by_user_id=app_user.id,
    )
    await state.clear()
    await message.answer(
        MKT_MATERIALS_CREATED.format(
            id=material.id,
            title=material.title,
            category=MATERIAL_CATEGORY_LABELS.get(material.category.value, material.category.value),
        ),
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
