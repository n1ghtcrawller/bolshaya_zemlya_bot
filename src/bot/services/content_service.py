from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ContentStatus, ContentType
from bot.db.models.content_item import ContentItem
from bot.db.repositories.content_item import ContentItemRepository


class ContentService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ContentItemRepository(session)

    async def list_by_type(self, content_type: ContentType) -> Sequence[ContentItem]:
        return await self._repo.list_by_type(content_type)

    async def create(
        self,
        *,
        content_type: ContentType,
        title: str,
        body: str | None,
        region: str | None,
        scheduled_at: datetime | None,
        author_user_id: int | None,
    ) -> ContentItem:
        status = (
            ContentStatus.SCHEDULED
            if scheduled_at is not None or content_type == ContentType.SCHEDULED
            else ContentStatus.DRAFT
        )
        return await self._repo.create(
            type_=content_type,
            title=title,
            body=body,
            region=region,
            scheduled_at=scheduled_at,
            author_user_id=author_user_id,
            status=status,
        )

    async def get(self, item_id: int) -> ContentItem | None:
        return await self._repo.get_by_id(item_id)
