import asyncio

import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from bot.api.handlers import build_root_router
from bot.api.middlewares import DbSessionMiddleware, RoleMiddleware
from bot.cache import build_redis
from bot.cache.role_cache import RoleCache
from bot.config import get_settings
from bot.db.session import build_engine, build_sessionmaker
from bot.logger import configure_logging, get_logger
from bot.services.content_publisher import publish_due_content
from bot.services.n8n_client import N8nClient


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.logging)
    log = get_logger("bot.main")

    engine = build_engine(settings.postgres)
    sessionmaker = build_sessionmaker(engine)
    redis = build_redis(settings.redis)
    role_cache = RoleCache(redis, settings.cache.role_cache_ttl)
    http_client = httpx.AsyncClient()
    n8n = N8nClient(settings.n8n, http_client)

    storage = RedisStorage(redis=redis)
    bot = Bot(
        settings.telegram.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    dp.update.outer_middleware(DbSessionMiddleware(sessionmaker))
    dp.update.outer_middleware(RoleMiddleware(role_cache))

    dp.include_router(build_root_router())

    # Workflow data — aiogram injects по имени параметра в хендлеры.
    dp["http_client"] = http_client
    dp["redis"] = redis
    dp["settings"] = settings
    dp["role_cache"] = role_cache

    scheduler = AsyncIOScheduler(timezone="UTC")
    if settings.publisher.enabled:
        scheduler.add_job(
            publish_due_content,
            trigger=IntervalTrigger(seconds=settings.publisher.interval_seconds),
            kwargs={"sessionmaker": sessionmaker, "n8n": n8n},
            id="content_publisher",
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        log.info(
            "content_publisher_scheduled",
            interval_seconds=settings.publisher.interval_seconds,
        )
    else:
        log.info("content_publisher_disabled")

    log.info("bot_started")
    try:
        await bot.delete_webhook(drop_pending_updates=settings.telegram.drop_pending_updates)
        await dp.start_polling(bot)
    finally:
        log.info("bot_stopping")
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await http_client.aclose()
        await bot.session.close()
        await redis.aclose()
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
