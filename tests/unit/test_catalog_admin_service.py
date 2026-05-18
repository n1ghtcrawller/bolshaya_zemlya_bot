import pytest

from bot.services.catalog_admin_service import CatalogAdminService, _slugify


def test_slugify_cyrillic_to_latin():
    # Транслитерация по таблице _TRANSLIT: х→kh, ч→ch, щ→sch, ь/ъ→""
    assert _slugify("Тракторы") == "traktory"
    assert _slugify("Сельхоз техника") == "selkhoz-tekhnika"
    assert _slugify("Запасные части") == "zapasnye-chasti"


def test_slugify_handles_special_chars():
    assert _slugify("  ABC / 123 !!!  ") == "abc-123"
    assert _slugify("---") == "category"
    assert _slugify("") == "category"


@pytest.mark.asyncio
async def test_unique_slug_appends_suffix(session):
    service = CatalogAdminService(session)
    a = await service.create_category(name="Тракторы")
    b = await service.create_category(name="Тракторы")
    c = await service.create_category(name="Тракторы")
    assert a.slug == "traktory"
    assert b.slug == "traktory-2"
    assert c.slug == "traktory-3"
