from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ApprovalStatus, SalesMaterialCategory, SalesMaterialFileType
from bot.db.models.sales_material import SalesMaterial
from bot.db.repositories.sales_material import SalesMaterialRepository
from bot.logger import get_logger

log = get_logger(__name__)


class MaterialModerationService:
    """Очередь модерации материалов. Используется Маркетингом."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SalesMaterialRepository(session)

    async def list_pending(self) -> Sequence[SalesMaterial]:
        return await self._repo.list_pending()

    async def get(self, material_id: int) -> SalesMaterial | None:
        return await self._repo.get_by_id(material_id)

    async def submit_for_review(
        self,
        *,
        category: SalesMaterialCategory,
        title: str,
        description: str | None,
        file_type: SalesMaterialFileType,
        telegram_file_id: str,
        uploaded_by_user_id: int,
    ) -> SalesMaterial:
        """Дилер загружает материал — статус PENDING до одобрения маркетингом."""
        material = await self._repo.create(
            category=category,
            title=title,
            description=description,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
            uploaded_by_user_id=uploaded_by_user_id,
            approval_status=ApprovalStatus.PENDING,
        )
        log.info(
            "material_submitted_for_review",
            material_id=material.id,
            dealer_id=uploaded_by_user_id,
        )
        return material

    async def approve(
        self, material_id: int, *, approved_by_user_id: int, note: str | None = None
    ) -> SalesMaterial | None:
        material = await self._repo.get_by_id(material_id)
        if material is None:
            return None
        return await self._repo.approve(
            material,
            approved_by_user_id=approved_by_user_id,
            approved_at=datetime.now(tz=timezone.utc),
            note=note,
        )

    async def reject(
        self, material_id: int, *, approved_by_user_id: int, note: str | None = None
    ) -> SalesMaterial | None:
        material = await self._repo.get_by_id(material_id)
        if material is None:
            return None
        return await self._repo.reject(
            material,
            approved_by_user_id=approved_by_user_id,
            approved_at=datetime.now(tz=timezone.utc),
            note=note,
        )
