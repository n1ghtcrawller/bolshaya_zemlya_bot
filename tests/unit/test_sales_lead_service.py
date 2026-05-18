import pytest

from bot.core.enums import LeadType, RequestStatus, UserRole
from bot.db.repositories.client_request import ClientRequestRepository
from bot.services.sales_lead_service import SalesLeadService


async def _make_lead(session, client_id, *, status=RequestStatus.NEW, assigned_sales_id=None):
    repo = ClientRequestRepository(session)
    lead = await repo.create(
        user_id=client_id,
        contact_name="Иван",
        contact_phone="+71234567890",
        comment=None,
        lead_type=LeadType.REQUEST,
    )
    if status != RequestStatus.NEW or assigned_sales_id is not None:
        lead.status = status
        lead.assigned_sales_id = assigned_sales_id
        await session.flush()
    return lead


@pytest.mark.asyncio
async def test_take_assigns_sales_and_sets_in_progress(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    await session.flush()
    lead = await _make_lead(session, client.id)

    result = await SalesLeadService(session).take(sales.id, lead.id)

    assert result is not None
    assert result.status is RequestStatus.IN_PROGRESS
    assert result.assigned_sales_id == sales.id


@pytest.mark.asyncio
async def test_take_does_nothing_if_already_taken(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales_a = make_user(session, role=UserRole.SALES)
    sales_b = make_user(session, role=UserRole.SALES)
    await session.flush()
    lead = await _make_lead(
        session, client.id, status=RequestStatus.IN_PROGRESS, assigned_sales_id=sales_a.id
    )

    result = await SalesLeadService(session).take(sales_b.id, lead.id)

    assert result is not None
    # лид остался у sales_a
    assert result.assigned_sales_id == sales_a.id


@pytest.mark.asyncio
async def test_transfer_requires_owner(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales_owner = make_user(session, role=UserRole.SALES)
    sales_intruder = make_user(session, role=UserRole.SALES)
    dealer = make_user(session, role=UserRole.DEALER)
    await session.flush()
    lead = await _make_lead(
        session, client.id, status=RequestStatus.IN_PROGRESS, assigned_sales_id=sales_owner.id
    )

    # Чужой sales не может передать
    bad = await SalesLeadService(session).transfer_to_dealer(
        sales_intruder.id, lead.id, dealer.id
    )
    assert bad is None

    # Владелец передаёт
    ok = await SalesLeadService(session).transfer_to_dealer(
        sales_owner.id, lead.id, dealer.id
    )
    assert ok is not None
    assert ok.status is RequestStatus.TRANSFERRED_TO_DEALER
    assert ok.assigned_dealer_id == dealer.id


@pytest.mark.asyncio
async def test_keep_marks_kept_by_sales(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    await session.flush()
    lead = await _make_lead(
        session, client.id, status=RequestStatus.IN_PROGRESS, assigned_sales_id=sales.id
    )

    result = await SalesLeadService(session).keep(sales.id, lead.id)

    assert result is not None
    assert result.status is RequestStatus.KEPT_BY_SALES
    assert result.assigned_dealer_id is None


@pytest.mark.asyncio
async def test_reject_works_for_owner_and_unassigned(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    await session.flush()

    # NEW (без assigned_sales) — отклонить может любой sales (с присвоением себя)
    lead1 = await _make_lead(session, client.id)
    out1 = await SalesLeadService(session).reject(sales.id, lead1.id)
    assert out1 is not None
    assert out1.status is RequestStatus.REJECTED
    assert out1.assigned_sales_id == sales.id

    # IN_PROGRESS у sales — отклонить может владелец
    lead2 = await _make_lead(
        session, client.id, status=RequestStatus.IN_PROGRESS, assigned_sales_id=sales.id
    )
    out2 = await SalesLeadService(session).reject(sales.id, lead2.id)
    assert out2 is not None
    assert out2.status is RequestStatus.REJECTED
