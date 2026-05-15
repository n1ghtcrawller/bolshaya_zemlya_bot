from redis.asyncio import Redis

from bot.core.enums import UserRole


class RoleCache:
    """Кэш роли пользователя по telegram_id с TTL.

    Используется middleware для определения роли без похода в БД на каждое сообщение.
    """

    PREFIX = "user:role:"

    def __init__(self, redis: Redis, ttl_seconds: int) -> None:
        self._redis = redis
        self._ttl = ttl_seconds

    def _key(self, telegram_id: int) -> str:
        return f"{self.PREFIX}{telegram_id}"

    async def get(self, telegram_id: int) -> UserRole | None:
        raw = await self._redis.get(self._key(telegram_id))
        if raw is None:
            return None
        value = raw.decode() if isinstance(raw, bytes) else raw
        try:
            return UserRole(value)
        except ValueError:
            await self.invalidate(telegram_id)
            return None

    async def set(self, telegram_id: int, role: UserRole) -> None:
        await self._redis.set(self._key(telegram_id), role.value, ex=self._ttl)

    async def invalidate(self, telegram_id: int) -> None:
        await self._redis.delete(self._key(telegram_id))
