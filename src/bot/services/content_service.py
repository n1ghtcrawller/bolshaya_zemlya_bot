from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ContentStatus, ContentType, SalesMaterialFileType
from bot.db.models.content_item import ContentItem
from bot.db.repositories.content_item import ContentItemRepository
from bot.logger import get_logger

log = get_logger(__name__)


class ContentService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ContentItemRepository(session)

    async def list_by_type(self, content_type: ContentType) -> Sequence[ContentItem]:
        return await self._repo.list_by_type(content_type)

    async def list_pending(self) -> Sequence[ContentItem]:
        return await self._repo.list_pending()

    async def get(self, item_id: int) -> ContentItem | None:
        return await self._repo.get_by_id(item_id)

    async def create(
        self,
        *,
        content_type: ContentType,
        title: str,
        body: str | None,
        region: str | None,
        scheduled_at: datetime | None,
        author_user_id: int | None,
        file_type: SalesMaterialFileType | None = None,
        telegram_file_id: str | None = None,
        submit_for_approval: bool = False,
    ) -> ContentItem:
        if submit_for_approval:
            status = ContentStatus.PENDING_APPROVAL
        elif scheduled_at is not None:
            # SCHEDULED — это рабочий статус автопостинга; ставится только когда есть дата.
            # Тип контента ContentType.SCHEDULED («отложка») — отдельная ось, не определяет статус.
            status = ContentStatus.SCHEDULED
        else:
            status = ContentStatus.DRAFT
        item = await self._repo.create(
            type_=content_type,
            title=title,
            body=body,
            region=region,
            scheduled_at=scheduled_at,
            author_user_id=author_user_id,
            status=status,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
        )
        log.info(
            "content_created",
            id=item.id,
            type=content_type.value,
            status=status.value,
            has_media=telegram_file_id is not None,
        )
        return item

    async def approve(
        self, item_id: int, *, approved_by_user_id: int, note: str | None = None
    ) -> ContentItem | None:
        item = await self._repo.get_by_id(item_id)
        if item is None:
            return None
        return await self._repo.approve(
            item,
            approved_by_user_id=approved_by_user_id,
            approved_at=datetime.now(tz=timezone.utc),
            note=note,
        )

    async def reject(
        self, item_id: int, *, approved_by_user_id: int, note: str | None = None
    ) -> ContentItem | None:
        item = await self._repo.get_by_id(item_id)
        if item is None:
            return None
        return await self._repo.reject(
            item,
            approved_by_user_id=approved_by_user_id,
            approved_at=datetime.now(tz=timezone.utc),
            note=note,
        )

    async def submit_for_approval(self, item_id: int) -> ContentItem | None:
        item = await self._repo.get_by_id(item_id)
        if item is None:
            return None
        return await self._repo.update_status(item, ContentStatus.PENDING_APPROVAL)

    async def archive(self, item_id: int) -> ContentItem | None:
        item = await self._repo.get_by_id(item_id)
        if item is None:
            return None
        return await self._repo.update_status(item, ContentStatus.ARCHIVED)

    async def mark_published(self, item_id: int) -> ContentItem | None:
        item = await self._repo.get_by_id(item_id)
        if item is None:
            return None
        return await self._repo.update_status(item, ContentStatus.PUBLISHED)
