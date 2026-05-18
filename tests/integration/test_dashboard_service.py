import pytest

from bot.core.enums import LeadType, RequestStatus, UserRole
from bot.db.repositories.client_request import ClientRequestRepository
from bot.services.catalog_admin_service import CatalogAdminService
from bot.services.dashboard_service import DashboardService


async def _lead(session, client_id, *, product_id=None):
    return await ClientRequestRepository(session).create(
        user_id=client_id,
        contact_name="X",
        contact_phone="+71",
        comment=None,
        lead_type=LeadType.REQUEST,
        product_id=product_id,
    )


@pytest.mark.asyncio
async def test_snapshot_aggregates_users_and_leads(session, make_user):
    make_user(session, role=UserRole.CLIENT)
    make_user(session, role=UserRole.SALES)
    make_user(session, role=UserRole.SALES)
    make_user(session, role=UserRole.DEALER)
    await session.flush()
    client = make_user(session, role=UserRole.CLIENT)
    await session.flush()
    await _lead(session, client.id)
    await _lead(session, client.id)

    snap = await DashboardService(session).snapshot()

    assert snap.users_by_role.get(UserRole.SALES) == 2
    assert snap.users_by_role.get(UserRole.DEALER) == 1
    assert snap.users_by_role.get(UserRole.CLIENT) == 2
    assert snap.leads_by_status.get(RequestStatus.NEW) == 2


@pytest.mark.asyncio
async def test_dealers_breakdown_counts_by_status(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    dealer = make_user(session, role=UserRole.DEALER, full_name="Иванов")
    await session.flush()
    repo = ClientRequestRepository(session)

    done = await _lead(session, client.id)
    await repo.assign_dealer(done, dealer.id, RequestStatus.DONE)
    in_progress = await _lead(session, client.id)
    await repo.assign_dealer(in_progress, dealer.id, RequestStatus.IN_PROGRESS)
    transferred = await _lead(session, client.id)
    await repo.assign_dealer(transferred, dealer.id, RequestStatus.TRANSFERRED_TO_DEALER)

    rows = await DashboardService(session).dealers_breakdown()

    assert len(rows) == 1
    row = rows[0]
    assert row.dealer_id == dealer.id
    assert row.full_name == "Иванов"
    assert row.total == 3
    assert row.done == 1
    assert row.in_progress == 1
    assert row.transferred == 1
    assert row.rejected == 0


@pytest.mark.asyncio
async def test_top_products_groups_and_sorts(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    marketer = make_user(session, role=UserRole.MARKETING)
    await session.flush()

    admin = CatalogAdminService(session)
    cat = await admin.create_category(name="Тракторы")
    p1 = await admin.create_product(
        category_id=cat.id,
        name="Трактор XL-200",
        short_description=None,
        full_description=None,
        price_text=None,
        specs=None,
        main_photo_file_id=None,
        created_by_user_id=marketer.id,
    )
    p2 = await admin.create_product(
        category_id=cat.id,
        name="Трактор Mini",
        short_description=None,
        full_description=None,
        price_text=None,
        specs=None,
        main_photo_file_id=None,
        created_by_user_id=marketer.id,
    )
    await session.flush()

    # 3 заявки на p1, 1 на p2, 1 без продукта (в топ не попадает)
    await _lead(session, client.id, product_id=p1.id)
    await _lead(session, client.id, product_id=p1.id)
    await _lead(session, client.id, product_id=p1.id)
    await _lead(session, client.id, product_id=p2.id)
    await _lead(session, client.id, product_id=None)

    rows = await DashboardService(session).top_products()

    assert [r.product_id for r in rows] == [p1.id, p2.id]
    assert rows[0].requests_total == 3
    assert rows[0].category == "Тракторы"
    assert rows[1].requests_total == 1
