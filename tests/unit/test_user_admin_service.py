from unittest.mock import AsyncMock

import pytest

from bot.cache.role_cache import RoleCache
from bot.core.enums import UserRole
from bot.services.user_admin_service import UserAdminService


def _fake_role_cache() -> RoleCache:
    cache = RoleCache.__new__(RoleCache)  # bypass __init__
    cache.invalidate = AsyncMock()
    cache.set = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    return cache


@pytest.mark.asyncio
async def test_delete_requires_admin(session, make_user):
    actor = make_user(session, role=UserRole.MARKETING)
    target = make_user(session, role=UserRole.CLIENT)
    await session.flush()
    service = UserAdminService(session, _fake_role_cache())

    user, error = await service.delete(user_id=target.id, deleted_by=actor)

    assert user is None
    assert error == "forbidden"


@pytest.mark.asyncio
async def test_delete_self_blocked(session, make_user):
    admin = make_user(session, role=UserRole.ADMIN)
    await session.flush()
    service = UserAdminService(session, _fake_role_cache())

    user, error = await service.delete(user_id=admin.id, deleted_by=admin)

    assert user is not None
    assert error == "self_delete"


@pytest.mark.asyncio
async def test_delete_admin_removes_user_and_invalidates_cache(session, make_user):
    admin = make_user(session, role=UserRole.ADMIN)
    target = make_user(session, role=UserRole.CLIENT, telegram_id=555)
    await session.flush()
    cache = _fake_role_cache()
    service = UserAdminService(session, cache)

    deleted, error = await service.delete(user_id=target.id, deleted_by=admin)

    assert error is None
    assert deleted is not None
    assert deleted.telegram_id == 555
    cache.invalidate.assert_awaited_once_with(555)

    # повторная попытка не находит пользователя
    again, error2 = await service.delete(user_id=target.id, deleted_by=admin)
    assert again is None
    assert error2 == "not_found"
