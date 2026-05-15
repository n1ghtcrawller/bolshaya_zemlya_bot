from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, product_id: int) -> Product | None:
        return await self._session.get(Product, product_id)

    async def list_by_category(
        self, category_id: int, *, limit: int = 10, offset: int = 0
    ) -> Sequence[Product]:
        stmt = (
            select(Product)
            .where(Product.category_id == category_id, Product.is_active.is_(True))
            .order_by(Product.sort_order.asc(), Product.name.asc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_by_category(self, category_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Product)
            .where(Product.category_id == category_id, Product.is_active.is_(True))
        )
        return int(await self._session.scalar(stmt) or 0)

    async def create(
        self,
        *,
        category_id: int,
        name: str,
        short_description: str | None,
        full_description: str | None,
        price_text: str | None,
        specs: str | None,
        main_photo_file_id: str | None,
        created_by_user_id: int | None,
        sort_order: int = 0,
    ) -> Product:
        product = Product(
            category_id=category_id,
            name=name,
            short_description=short_description,
            full_description=full_description,
            price_text=price_text,
            specs=specs,
            main_photo_file_id=main_photo_file_id,
            created_by_user_id=created_by_user_id,
            sort_order=sort_order,
        )
        self._session.add(product)
        await self._session.flush()
        return product
