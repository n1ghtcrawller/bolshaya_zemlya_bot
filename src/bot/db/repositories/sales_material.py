from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ApprovalStatus, SalesMaterialCategory, SalesMaterialFileType
from bot.db.models.sales_material import SalesMaterial


class SalesMaterialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_category(
        self,
        category: SalesMaterialCategory,
        *,
        limit: int = 10,
        offset: int = 0,
        approval_status: ApprovalStatus | None = ApprovalStatus.APPROVED,
    ) -> Sequence[SalesMaterial]:
        stmt = select(SalesMaterial).where(
            SalesMaterial.category == category, SalesMaterial.is_active.is_(True)
        )
        if approval_status is not None:
            stmt = stmt.where(SalesMaterial.approval_status == approval_status)
        stmt = stmt.order_by(SalesMaterial.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.scalars(stmt)
        return result.all()

    async def count_by_category(
        self,
        category: SalesMaterialCategory,
        *,
        approval_status: ApprovalStatus | None = ApprovalStatus.APPROVED,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(SalesMaterial)
            .where(SalesMaterial.category == category, SalesMaterial.is_active.is_(True))
        )
        if approval_status is not None:
            stmt = stmt.where(SalesMaterial.approval_status == approval_status)
        return int(await self._session.scalar(stmt) or 0)

    async def list_pending(self, *, limit: int = 20) -> Sequence[SalesMaterial]:
        stmt = (
            select(SalesMaterial)
            .where(SalesMaterial.approval_status == ApprovalStatus.PENDING)
            .order_by(SalesMaterial.created_at.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def get_by_id(self, material_id: int) -> SalesMaterial | None:
        return await self._session.get(SalesMaterial, material_id)

    async def create(
        self,
        *,
        category: SalesMaterialCategory,
        title: str,
        description: str | None,
        file_type: SalesMaterialFileType,
        telegram_file_id: str,
        uploaded_by_user_id: int | None,
        approval_status: ApprovalStatus = ApprovalStatus.APPROVED,
    ) -> SalesMaterial:
        material = SalesMaterial(
            category=category,
            title=title,
            description=description,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
            uploaded_by_user_id=uploaded_by_user_id,
            approval_status=approval_status,
        )
        self._session.add(material)
        await self._session.flush()
        return material

    async def approve(
        self,
        material: SalesMaterial,
        *,
        approved_by_user_id: int,
        approved_at: datetime,
        note: str | None = None,
    ) -> SalesMaterial:
        material.approval_status = ApprovalStatus.APPROVED
        material.approved_by_user_id = approved_by_user_id
        material.approved_at = approved_at
        if note is not None:
            material.approval_note = note
        await self._session.flush()
        return material

    async def reject(
        self,
        material: SalesMaterial,
        *,
        approved_by_user_id: int,
        approved_at: datetime,
        note: str | None = None,
    ) -> SalesMaterial:
        material.approval_status = ApprovalStatus.REJECTED
        material.approved_by_user_id = approved_by_user_id
        material.approved_at = approved_at
        if note is not None:
            material.approval_note = note
        await self._session.flush()
        return material
