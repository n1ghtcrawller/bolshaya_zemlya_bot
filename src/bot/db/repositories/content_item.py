from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ContentStatus, ContentType
from bot.db.models.content_item import ContentItem


class ContentItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: int) -> ContentItem | None:
        return await self._session.get(ContentItem, item_id)

    async def list_by_type(
        self, content_type: ContentType, *, limit: int = 20, offset: int = 0
    ) -> Sequence[ContentItem]:
        stmt = (
            select(ContentItem)
            .where(ContentItem.type == content_type)
            .order_by(ContentItem.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._session.scalars(stmt)).all()

    async def create(
        self,
        *,
        type_: ContentType,
        title: str,
        body: str | None,
        region: str | None,
        scheduled_at: datetime | None,
        author_user_id: int | None,
        status: ContentStatus = ContentStatus.DRAFT,
    ) -> ContentItem:
        item = ContentItem(
            type=type_,
            title=title,
            body=body,
            region=region,
            scheduled_at=scheduled_at,
            author_user_id=author_user_id,
            status=status,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def update_status(self, item: ContentItem, status: ContentStatus) -> ContentItem:
        item.status = status
        await self._session.flush()
        return item
