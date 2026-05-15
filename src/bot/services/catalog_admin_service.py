import re

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.product import Product
from bot.db.models.product_category import ProductCategory
from bot.db.repositories.product import ProductRepository
from bot.db.repositories.product_category import ProductCategoryRepository


class CatalogAdminService:
    """Управление каталогом для Маркетинга/Админа."""

    def __init__(self, session: AsyncSession) -> None:
        self._categories = ProductCategoryRepository(session)
        self._products = ProductRepository(session)

    async def create_category(self, *, name: str) -> ProductCategory:
        slug = await self._unique_slug(name)
        return await self._categories.create(name=name, slug=slug)

    async def create_product(
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
    ) -> Product:
        return await self._products.create(
            category_id=category_id,
            name=name,
            short_description=short_description,
            full_description=full_description,
            price_text=price_text,
            specs=specs,
            main_photo_file_id=main_photo_file_id,
            created_by_user_id=created_by_user_id,
        )

    async def _unique_slug(self, name: str) -> str:
        base = _slugify(name)
        candidate = base
        suffix = 1
        while await self._categories.get_by_slug(candidate) is not None:
            suffix += 1
            candidate = f"{base}-{suffix}"
        return candidate


_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _slugify(value: str) -> str:
    lower = value.strip().lower()
    transliterated = "".join(_TRANSLIT.get(ch, ch) for ch in lower)
    cleaned = re.sub(r"[^a-z0-9]+", "-", transliterated).strip("-")
    return cleaned or "category"
