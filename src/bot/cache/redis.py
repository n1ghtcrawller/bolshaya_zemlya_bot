from redis.asyncio import Redis

from bot.config import RedisSettings


def build_redis(settings: RedisSettings) -> Redis:
    """Один shared Redis-клиент: используется и aiogram RedisStorage (FSM), и RoleCache.

    decode_responses=False — обязательно, иначе RedisStorage ломается на bytes/str.
    Чтение строковых значений в коде делаем явно через .decode().
    """
    return Redis.from_url(settings.url, decode_responses=False)
