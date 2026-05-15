from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.cache.role_cache import RoleCache
from bot.core.enums import UserRole
from bot.db.models.user import User
from bot.db.repositories.user import UserRepository
from bot.logger import get_logger

log = get_logger(__name__)


class UserAdminService:
    """Управление пользователями для роли Маркетинг/Админ.

    При смене роли инвалидирует Redis-кэш, чтобы новая роль применилась с первого же
    апдейта (иначе нужно ждать ROLE_CACHE_TTL).
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
