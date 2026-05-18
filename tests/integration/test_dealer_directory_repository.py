import pytest

from bot.core.enums import UserRole
from bot.db.repositories.dealer_directory import DealerDirectoryRepository
from bot.db.repositories.dealer_profile import DealerProfileRepository


@pytest.mark.asyncio
async def test_directory_lists_unique_regions(session, make_user):
    dealer_a = make_user(session, role=UserRole.DEALER, full_name="A")
    dealer_b = make_user(session, role=UserRole.DEALER, full_name="B")
    dealer_no_region = make_user(session, role=UserRole.DEALER, full_name="C")
    inactive_dealer = make_user(
        session, role=UserRole.DEALER, full_name="D", is_active=False
    )
    sales = make_user(session, role=UserRole.SALES, full_name="not dealer")
    await session.flush()

    profiles = DealerProfileRepository(session)
    await profiles.update_fields(user_id=dealer_a.id, fields={"region": "Москва"})
    await profiles.update_fields(user_id=dealer_b.id, fields={"region": "Казань"})
    # dealer_no_region: профиль есть, но регион None — попадать не должен
    await profiles.update_fields(user_id=dealer_no_region.id, fields={"phone": "+7"})
    # inactive dealer — не показывается
    await profiles.update_fields(user_id=inactive_dealer.id, fields={"region": "Сочи"})
    # У sales может быть профиль другого типа — он не дилер, не показывается
    await session.flush()

    regions = await DealerDirectoryRepository(session).list_regions()
    assert set(regions) == {"Казань", "Москва"}


@pytest.mark.asyncio
async def test_list_by_region_returns_dealer_with_profile(session, make_user):
    dealer = make_user(session, role=UserRole.DEALER, full_name="Иванов")
    await session.flush()
    await DealerProfileRepository(session).update_fields(
        user_id=dealer.id,
        fields={"region": "Москва", "company": "ООО Иванов"},
    )
    await session.flush()

    rows = await DealerDirectoryRepository(session).list_by_region("Москва")

    assert len(rows) == 1
    user, profile = rows[0]
    assert user.id == dealer.id
    assert profile.company == "ООО Иванов"
