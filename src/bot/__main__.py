import asyncio

import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from bot.api.handlers import build_root_router
from bot.api.middlewares import DbSessionMiddleware, RoleMiddleware
from bot.cache import build_redis
from bot.cache.role_cache import RoleCache
from bot.config import get_settings
from bot.db.session import build_engine, build_sessionmaker
from bot.logger import configure_logging, get_logger


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.logging)
    log = get_logger("bot.main")

    engine = build_engine(settings.postgres)
    sessionmaker = build_sessionmaker(engine)
    redis = build_redis(settings.redis)
    role_cache = RoleCache(redis, settings.cache.role_cache_ttl)
    http_client = httpx.AsyncClient()

    storage = RedisStorage(redis=redis)
    bot = Bot(
        settings.telegram.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    dp.update.outer_middleware(DbSessionMiddleware(sessionmaker))
    dp.update.outer_middleware(RoleMiddleware(role_cache))

    dp.include_router(build_root_router())

    # Делаем httpx-клиент и redis доступными в data для будущих хендлеров (n8n).
    dp["http_client"] = http_client
    dp["redis"] = redis
    dp["settings"] = settings
    dp["role_cache"] = role_cache

    log.info("bot_started")
    try:
        await bot.delete_webhook(drop_pending_updates=settings.telegram.drop_pending_updates)
        await dp.start_polling(bot)
    finally:
        log.info("bot_stopping")
        await http_client.aclose()
        await bot.session.close()
        await redis.aclose()
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
