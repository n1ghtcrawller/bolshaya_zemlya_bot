from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import SalesMaterialCategory, SalesMaterialFileType
from bot.db.models.sales_material import SalesMaterial
from bot.db.repositories.sales_material import SalesMaterialRepository


class MaterialUploadService:
    """Маркетолог загружает продающие материалы, дилеры видят их в подменю."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SalesMaterialRepository(session)

    async def upload(
        self,
        *,
        category: SalesMaterialCategory,
        title: str,
        description: str | None,
        file_type: SalesMaterialFileType,
        telegram_file_id: str,
        uploaded_by_user_id: int | None,
    ) -> SalesMaterial:
        return await self._repo.create(
            category=category,
            title=title,
            description=description,
            file_type=file_type,
            telegram_file_id=telegram_file_id,
            uploaded_by_user_id=uploaded_by_user_id,
        )
