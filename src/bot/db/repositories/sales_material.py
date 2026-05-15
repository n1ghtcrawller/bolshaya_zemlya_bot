from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import SalesMaterialCategory, SalesMaterialFileType
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
    ) -> Sequence[SalesMaterial]:
        stmt = (
            select(SalesMaterial)
            .where(SalesMaterial.category == category, SalesMaterial.is_active.is_(True))
            .order_by(SalesMaterial.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.scalars(stmt)
        return result.all()

    async def count_by_category(self, category: SalesMaterialCategory) -> int:
        stmt = (
            select(func.count())
            .select_from(SalesMaterial)
            .where(SalesMaterial.category == category, SalesMaterial.is_active.is_(True))
        )
        return int(await self._session.scalar(stmt) or 0)

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
    ) -> SalesMaterial:
        material = SalesMaterial(
            category=category,
            title=title,
            description=description,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        self._session.add(material)
        await self._session.flush()
        return material
