from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ContentStatus, ContentType, SalesMaterialFileType
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

    async def list_pending(self, *, limit: int = 50) -> Sequence[ContentItem]:
        stmt = (
            select(ContentItem)
            .where(ContentItem.status == ContentStatus.PENDING_APPROVAL)
            .order_by(ContentItem.created_at.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def list_due_for_publish(
        self, now: datetime, *, limit: int = 50
    ) -> Sequence[ContentItem]:
        """Кандидаты на автопостинг: scheduled/approved с наступившим scheduled_at."""
        stmt = (
            select(ContentItem)
            .where(
                ContentItem.status.in_(
                    (ContentStatus.SCHEDULED, ContentStatus.APPROVED)
                ),
                ContentItem.scheduled_at.is_not(None),
                ContentItem.scheduled_at <= now,
            )
            .order_by(ContentItem.scheduled_at.asc())
            .limit(limit)
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
        file_type: SalesMaterialFileType | None = None,
        telegram_file_id: str | None = None,
    ) -> ContentItem:
        item = ContentItem(
            type=type_,
            title=title,
            body=body,
            region=region,
            scheduled_at=scheduled_at,
            author_user_id=author_user_id,
            status=status,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def update_status(self, item: ContentItem, status: ContentStatus) -> ContentItem:
        item.status = status
        await self._session.flush()
        return item

    async def approve(
        self,
        item: ContentItem,
        *,
        approved_by_user_id: int,
        approved_at: datetime,
        note: str | None = None,
    ) -> ContentItem:
        item.status = ContentStatus.APPROVED
        item.approved_by_user_id = approved_by_user_id
        item.approved_at = approved_at
        if note is not None:
            item.approval_note = note
        await self._session.flush()
        return item

    async def reject(
        self,
        item: ContentItem,
        *,
        approved_by_user_id: int,
        approved_at: datetime,
        note: str | None = None,
    ) -> ContentItem:
        item.status = ContentStatus.REJECTED
        item.approved_by_user_id = approved_by_user_id
        item.approved_at = approved_at
        if note is not None:
            item.approval_note = note
        await self._session.flush()
        return item
