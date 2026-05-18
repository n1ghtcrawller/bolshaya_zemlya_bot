import pytest

from bot.core.enums import LeadType, RequestStatus, UserRole
from bot.db.repositories.client_request import ClientRequestRepository


async def _new_lead(session, client_id):
    return await ClientRequestRepository(session).create(
        user_id=client_id,
        contact_name="X",
        contact_phone="+71234567890",
        comment=None,
        lead_type=LeadType.REQUEST,
    )


@pytest.mark.asyncio
async def test_list_unassigned_returns_only_new_without_assignment(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    await session.flush()
    repo = ClientRequestRepository(session)

    new_lead = await _new_lead(session, client.id)
    taken = await _new_lead(session, client.id)
    await repo.assign_sales(taken, sales.id, RequestStatus.IN_PROGRESS)

    result = await repo.list_unassigned()

    assert [l.id for l in result] == [new_lead.id]


@pytest.mark.asyncio
async def test_list_by_dealer_filters_by_assignment_and_status(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    dealer_a = make_user(session, role=UserRole.DEALER)
    dealer_b = make_user(session, role=UserRole.DEALER)
    await session.flush()
    repo = ClientRequestRepository(session)

    # лид для dealer_a
    lead_a = await _new_lead(session, client.id)
    await repo.assign_dealer(lead_a, dealer_a.id, RequestStatus.TRANSFERRED_TO_DEALER)
    # лид для dealer_b
    lead_b = await _new_lead(session, client.id)
    await repo.assign_dealer(lead_b, dealer_b.id, RequestStatus.TRANSFERRED_TO_DEALER)
    # лид без диллера
    await _new_lead(session, client.id)

    result_a = await repo.list_by_dealer(dealer_a.id)
    assert [l.id for l in result_a] == [lead_a.id]

    result_a_filtered = await repo.list_by_dealer(
        dealer_a.id, statuses=[RequestStatus.DONE]
    )
    assert list(result_a_filtered) == []


@pytest.mark.asyncio
async def test_count_grouped_returns_status_counts(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    dealer = make_user(session, role=UserRole.DEALER)
    await session.flush()
    repo = ClientRequestRepository(session)

    new_lead = await _new_lead(session, client.id)
    in_progress = await _new_lead(session, client.id)
    await repo.assign_sales(in_progress, sales.id, RequestStatus.IN_PROGRESS)
    transferred = await _new_lead(session, client.id)
    await repo.assign_dealer(transferred, dealer.id, RequestStatus.TRANSFERRED_TO_DEALER)

    counts = await repo.count_grouped()

    assert counts.get(RequestStatus.NEW) == 1
    assert counts.get(RequestStatus.IN_PROGRESS) == 1
    assert counts.get(RequestStatus.TRANSFERRED_TO_DEALER) == 1
    # sanity: new_lead остался NEW
    assert new_lead.status is RequestStatus.NEW
