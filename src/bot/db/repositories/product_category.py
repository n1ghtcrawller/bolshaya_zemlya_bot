from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.product_category import ProductCategory


class ProductCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, category_id: int) -> ProductCategory | None:
        return await self._session.get(ProductCategory, category_id)

    async def get_by_slug(self, slug: str) -> ProductCategory | None:
        stmt = select(ProductCategory).where(ProductCategory.slug == slug)
        return await self._session.scalar(stmt)

    async def list_active(self) -> Sequence[ProductCategory]:
        stmt = (
            select(ProductCategory)
            .where(ProductCategory.is_active.is_(True))
            .order_by(ProductCategory.sort_order.asc(), ProductCategory.name.asc())
        )
        return (await self._session.scalars(stmt)).all()

    async def create(
        self, *, name: str, slug: str, sort_order: int = 0
    ) -> ProductCategory:
        category = ProductCategory(name=name, slug=slug, sort_order=sort_order)
        self._session.add(category)
        await self._session.flush()
        return category
