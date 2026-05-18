from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.cache.role_cache import RoleCache
from bot.core.enums import UserRole
from bot.db.models.user import User
from bot.db.repositories.user import UserRepository
from bot.logger import get_logger

log = get_logger(__name__)


class UserAdminService:
    """Управление пользователями для роли Маркетинг / HeadOfMarketing / Admin.

    При смене или удалении инвалидирует Redis-кэш, чтобы изменение применилось
    с первого же апдейта (иначе нужно ждать ROLE_CACHE_TTL).
    """

    def __init__(self, session: AsyncSession, role_cache: RoleCache) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._role_cache = role_cache

    async def list_by_role(self, role: UserRole) -> Sequence[User]:
        return await self._users.list_by_role(role)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._users.get_by_id(user_id)

    async def set_role(self, user_id: int, role: UserRole) -> User | None:
        user = await self._users.get_by_id(user_id)
        if user is None:
            return None
        previous = user.role
        await self._users.set_role(user, role)
        await self._role_cache.invalidate(user.telegram_id)
        log.info(
            "user_role_changed",
            user_id=user.id,
            telegram_id=user.telegram_id,
            previous=previous.value,
            new=role.value,
        )
        return user

    async def delete(
        self, *, user_id: int, deleted_by: User
    ) -> tuple[User | None, str | None]:
        """Удаляет пользователя со всеми связанными данными (через CASCADE).

        Возвращает (deleted_user, error). Возможные error:
        - 'forbidden' — у инициатора нет роли ADMIN
        - 'not_found' — пользователь не существует
        - 'self_delete' — попытка удалить самого себя
        """
        if deleted_by.role is not UserRole.ADMIN:
            return None, "forbidden"
        target = await self._users.get_by_id(user_id)
        if target is None:
            return None, "not_found"
        if target.id == deleted_by.id:
            return target, "self_delete"

        await self._role_cache.invalidate(target.telegram_id)
        await self._session.delete(target)
        await self._session.flush()
        log.info(
            "user_deleted",
            user_id=target.id,
            telegram_id=target.telegram_id,
            deleted_by=deleted_by.id,
        )
        return target, None
