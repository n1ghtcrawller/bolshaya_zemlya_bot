from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.product import Product
from bot.db.models.product_category import ProductCategory
from bot.db.repositories.product import ProductRepository
from bot.db.repositories.product_category import ProductCategoryRepository


class CatalogService:
    """Чтение каталога продукции. Используется Клиентом, Диллером и Sales."""

    PAGE_SIZE = 5

    def __init__(self, session: AsyncSession) -> None:
        self._categories = ProductCategoryRepository(session)
        self._products = ProductRepository(session)

    async def list_categories(self) -> Sequence[ProductCategory]:
        return await self._categories.list_active()

    async def get_category(self, category_id: int) -> ProductCategory | None:
        return await self._categories.get_by_id(category_id)

    async def get_product(self, product_id: int) -> Product | None:
        product = await self._products.get_by_id(product_id)
        if product is None or not product.is_active:
            return None
        return product

    async def page(
        self, category_id: int, page: int
    ) -> tuple[Sequence[Product], int, int]:
        page = max(page, 0)
        total = await self._products.count_by_category(category_id)
        if total == 0:
            return [], 0, 0
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = min(page, pages - 1)
        items = await self._products.list_by_category(
            category_id, limit=self.PAGE_SIZE, offset=page * self.PAGE_SIZE
        )
        return items, page, pages
