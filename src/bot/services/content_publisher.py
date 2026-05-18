"""Фоновый воркер автопостинга контента через n8n.

Запускается AsyncIOScheduler-ом раз в `PUBLISHER_INTERVAL_SECONDS` секунд.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.core.enums import ContentStatus
from bot.core.exceptions import N8nUnavailableError
from bot.db.models.content_item import ContentItem
from bot.db.repositories.content_item import ContentItemRepository
from bot.logger import get_logger
from bot.services.n8n_client import N8nClient

log = get_logger(__name__)


def _payload(item: ContentItem) -> dict:
    return {
        "content_id": item.id,
        "type": item.type.value,
        "title": item.title,
        "body": item.body,
        "region": item.region,
        "scheduled_at": item.scheduled_at.isoformat() if item.scheduled_at else None,
        "file_type": item.file_type.value if item.file_type else None,
        "telegram_file_id": item.telegram_file_id,
    }


async def _publish_one(
    session: AsyncSession, item: ContentItem, n8n: N8nClient
) -> bool:
    repo = ContentItemRepository(session)
    try:
        await n8n.content_publish(_payload(item))
    except N8nUnavailableError as exc:
        log.warning(
            "content_publish_failed", content_id=item.id, error=str(exc)
        )
        return False

    await repo.update_status(item, ContentStatus.PUBLISHED)
    log.info("content_published", content_id=item.id, type=item.type.value)
    return True


async def publish_due_content(
    sessionmaker: async_sessionmaker[AsyncSession],
    n8n: N8nClient,
) -> int:
    """Один цикл публикации. Возвращает количество успешно опубликованных записей."""
    now = datetime.now(tz=timezone.utc)
    published = 0
    async with sessionmaker() as session:
        repo = ContentItemRepository(session)
        items = await repo.list_due_for_publish(now)
        if not items:
            return 0
        log.info("content_publisher_tick", candidates=len(items))
        for item in items:
            ok = await _publish_one(session, item, n8n)
            if ok:
                published += 1
        await session.commit()
    return published
