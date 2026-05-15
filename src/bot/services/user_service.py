from sqlalchemy.ext.asyncio import AsyncSession

from bot.cache.role_cache import RoleCache
from bot.core.enums import UserRole
from bot.db.models.user import User
from bot.db.repositories.client_profile import ClientProfileRepository
from bot.db.repositories.user import UserRepository
from bot.logger import get_logger
from bot.schemas.client import ClientProfileUpdate
from bot.schemas.user import TelegramUserData

log = get_logger(__name__)


class UserService:
    """Бизнес-логика по пользователям: создание/обновление, определение роли с кэшем."""

    def __init__(self, session: AsyncSession, role_cache: RoleCache) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._profiles = ClientProfileRepository(session)
        self._role_cache = role_cache

    async def get_or_create(self, data: TelegramUserData) -> tuple[User, bool]:
        """Возвращает (user, created). Создаёт запись с ролью CLIENT если её нет."""
        user = await self._users.get_by_telegram_id(data.telegram_id)
        if user is not None:
            if (
                user.full_name != data.full_name
                or user.username != data.username
                or user.language_code != data.language_code
            ):
                await self._users.update_profile_fields(
                    user,
                    full_name=data.full_name,
                    username=data.username,
                    language_code=data.language_code,
                )
            await self._role_cache.set(user.telegram_id, user.role)
            return user, False

        user = await self._users.create(
            telegram_id=data.telegram_id,
            full_name=data.full_name,
            username=data.username,
            language_code=data.language_code,
            role=UserRole.CLIENT,
        )
        await self._profiles.upsert(user_id=user.id)
        await self._role_cache.set(user.telegram_id, user.role)
        log.info("user_created", telegram_id=user.telegram_id, role=user.role.value)
        return user, True

    async def resolve_role(self, telegram_id: int) -> UserRole | None:
        cached = await self._role_cache.get(telegram_id)
        if cached is not None:
            return cached
        user = await self._users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        await self._role_cache.set(telegram_id, user.role)
        return user.role

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self._users.get_by_telegram_id(telegram_id)

    async def update_client_profile(self, user_id: int, payload: ClientProfileUpdate) -> None:
        await self._profiles.upsert(
            user_id=user_id,
            phone=payload.phone,
            region=payload.region,
            company=payload.company,
            email=payload.email,
        )
