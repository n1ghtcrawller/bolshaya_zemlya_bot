from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.keyboards.marketing import (
    CB_USER_SET_ROLE,
    CB_USER_VIEW,
    CB_USERS_ROLE,
    MktMenuCallback,
    back_to_menu,
    roles_kb,
    user_card_kb,
    user_pick_role_kb,
    users_list_kb,
)
from bot.api.texts import (
    MKT_USER_CARD,
    MKT_USER_NOT_FOUND,
    MKT_USER_PICK_NEW_ROLE,
    MKT_USER_ROLE_UPDATED,
    MKT_USERS_LIST_HEADER,
    MKT_USERS_PICK_ROLE,
    ROLE_LABELS,
)
from bot.cache.role_cache import RoleCache
from bot.core.enums import UserRole
from bot.services.user_admin_service import UserAdminService

users_router = Router(name="marketing.users")


@users_router.callback_query(F.data == MktMenuCallback.USERS)
async def pick_role(call: CallbackQuery) -> None:
    await call.answer()
    if call.message is None:
        return
    await call.message.answer(
        MKT_USERS_PICK_ROLE, reply_markup=roles_kb(CB_USERS_ROLE)
    )


@users_router.callback_query(F.data.startswith(f"{CB_USERS_ROLE}:"))
async def list_users(
    call: CallbackQuery, session: AsyncSession, role_cache: RoleCache
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    role = _parse_role(call.data.rsplit(":", 1)[-1])
    if role is None:
        return
    service = UserAdminService(session, role_cache)
    users = await service.list_by_role(role)
    header = MKT_USERS_LIST_HEADER.format(
        role=ROLE_LABELS[role.value], total=len(users)
    )
    if not users:
        await call.message.answer(header, reply_markup=back_to_menu())
        return
    body_lines = [header, ""]
    for user in users:
        body_lines.append(f"• #{user.id} {user.full_name} (TG: {user.telegram_id})")
    await call.message.answer(
        "\n".join(body_lines), reply_markup=users_list_kb([u.id for u in users])
    )


@users_router.callback_query(F.data.startswith(f"{CB_USER_VIEW}:open:"))
async def view_user(
    call: CallbackQuery, session: AsyncSession, role_cache: RoleCache
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    user_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if user_id is None:
        return
    service = UserAdminService(session, role_cache)
    user = await service.get_by_id(user_id)
    if user is None:
        await call.message.answer(MKT_USER_NOT_FOUND, reply_markup=back_to_menu())
        return
    text = MKT_USER_CARD.format(
        id=user.id,
        full_name=user.full_name,
        username=user.username or "—",
        telegram_id=user.telegram_id,
        role=ROLE_LABELS.get(user.role.value, user.role.value),
        created_at=user.created_at,
    )
    await call.message.answer(text, reply_markup=user_card_kb(user.id))


@users_router.callback_query(F.data.startswith(f"{CB_USER_VIEW}:setrole:"))
async def show_role_options(
    call: CallbackQuery, session: AsyncSession, role_cache: RoleCache
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    user_id = _parse_int(call.data.rsplit(":", 1)[-1])
    if user_id is None:
        return
    service = UserAdminService(session, role_cache)
    user = await service.get_by_id(user_id)
    if user is None:
        await call.message.answer(MKT_USER_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        MKT_USER_PICK_NEW_ROLE.format(full_name=user.full_name),
        reply_markup=user_pick_role_kb(user.id),
    )


@users_router.callback_query(F.data.startswith(f"{CB_USER_SET_ROLE}:"))
async def set_role(
    call: CallbackQuery, session: AsyncSession, role_cache: RoleCache
) -> None:
    await call.answer()
    if call.message is None or call.data is None:
        return
    parts = call.data.split(":")
    if len(parts) != 5:
        return
    user_id = _parse_int(parts[-2])
    role = _parse_role(parts[-1])
    if user_id is None or role is None:
        return
    service = UserAdminService(session, role_cache)
    user = await service.set_role(user_id, role)
    if user is None:
        await call.message.answer(MKT_USER_NOT_FOUND, reply_markup=back_to_menu())
        return
    await call.message.answer(
        MKT_USER_ROLE_UPDATED.format(
            full_name=user.full_name, role=ROLE_LABELS[role.value]
        ),
        reply_markup=back_to_menu(),
    )


def _parse_role(raw: str) -> UserRole | None:
    try:
        return UserRole(raw)
    except ValueError:
        return None


def _parse_int(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None
