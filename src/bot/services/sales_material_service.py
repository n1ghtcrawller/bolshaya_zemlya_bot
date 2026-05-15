from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import SalesMaterialCategory
from bot.db.models.sales_material import SalesMaterial
from bot.db.repositories.sales_material import SalesMaterialRepository


class SalesMaterialService:
    PAGE_SIZE = 5

    def __init__(self, session: AsyncSession) -> None:
        self._materials = SalesMaterialRepository(session)

    async def get_page(
        self, category: SalesMaterialCategory, page: int
    ) -> tuple[Sequence[SalesMaterial], int, int]:
        page = max(page, 0)
        total = await self._materials.count_by_category(category)
        if total == 0:
            return [], 0, 0
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = min(page, pages - 1)
        items = await self._materials.list_by_category(
            category, limit=self.PAGE_SIZE, offset=page * self.PAGE_SIZE
        )
        return items, page, pages

    async def get(self, material_id: int) -> SalesMaterial | None:
        return await self._materials.get_by_id(material_id)
