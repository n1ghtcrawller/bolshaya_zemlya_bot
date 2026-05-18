import pytest

from bot.core.enums import ApprovalStatus, LeadType, RequestStatus, UserRole
from bot.db.repositories.client_request import ClientRequestRepository
from bot.services.lead_approval_service import LeadApprovalService


async def _take_lead(session, client_id, sales_id):
    repo = ClientRequestRepository(session)
    lead = await repo.create(
        user_id=client_id,
        contact_name="Иван",
        contact_phone="+71234567890",
        comment=None,
        lead_type=LeadType.REQUEST,
    )
    await repo.assign_sales(lead, sales_id, RequestStatus.IN_PROGRESS)
    return lead


@pytest.mark.asyncio
async def test_request_requires_in_progress_owner(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    sales_other = make_user(session, role=UserRole.SALES)
    dealer = make_user(session, role=UserRole.DEALER)
    await session.flush()
    lead = await _take_lead(session, client.id, sales.id)
    svc = LeadApprovalService(session)

    # Чужой sales не может
    a, err = await svc.request(
        sales_user_id=sales_other.id, lead_id=lead.id, proposed_dealer_id=dealer.id
    )
    assert a is None
    assert err == "not_owner"

    # Владелец может
    a, err = await svc.request(
        sales_user_id=sales.id, lead_id=lead.id, proposed_dealer_id=dealer.id
    )
    assert a is not None
    assert err is None
    assert a.status is ApprovalStatus.PENDING


@pytest.mark.asyncio
async def test_duplicate_request_blocked(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    dealer = make_user(session, role=UserRole.DEALER)
    await session.flush()
    lead = await _take_lead(session, client.id, sales.id)
    svc = LeadApprovalService(session)

    a, _ = await svc.request(
        sales_user_id=sales.id, lead_id=lead.id, proposed_dealer_id=dealer.id
    )
    assert a is not None

    dup, err = await svc.request(
        sales_user_id=sales.id, lead_id=lead.id, proposed_dealer_id=dealer.id
    )
    assert dup is None
    assert err == "duplicate_pending"


@pytest.mark.asyncio
async def test_approve_transfers_lead_to_dealer(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    dealer = make_user(session, role=UserRole.DEALER)
    head = make_user(session, role=UserRole.HEAD_OF_SALES)
    await session.flush()
    lead = await _take_lead(session, client.id, sales.id)
    svc = LeadApprovalService(session)
    approval, _ = await svc.request(
        sales_user_id=sales.id, lead_id=lead.id, proposed_dealer_id=dealer.id
    )

    decided, err = await svc.approve(approval.id, head_user_id=head.id)

    assert err is None
    assert decided.status is ApprovalStatus.APPROVED
    assert decided.decision_by_user_id == head.id

    # Лид реально передан дилеру
    fresh = await ClientRequestRepository(session).get_by_id(lead.id)
    assert fresh.status is RequestStatus.TRANSFERRED_TO_DEALER
    assert fresh.assigned_dealer_id == dealer.id


@pytest.mark.asyncio
async def test_reject_keeps_lead_in_progress(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    dealer = make_user(session, role=UserRole.DEALER)
    head = make_user(session, role=UserRole.HEAD_OF_SALES)
    await session.flush()
    lead = await _take_lead(session, client.id, sales.id)
    svc = LeadApprovalService(session)
    approval, _ = await svc.request(
        sales_user_id=sales.id, lead_id=lead.id, proposed_dealer_id=dealer.id
    )

    decided, _ = await svc.reject(approval.id, head_user_id=head.id, note="не тот регион")

    assert decided.status is ApprovalStatus.REJECTED
    assert decided.decision_note == "не тот регион"
    fresh = await ClientRequestRepository(session).get_by_id(lead.id)
    assert fresh.status is RequestStatus.IN_PROGRESS
    assert fresh.assigned_dealer_id is None


@pytest.mark.asyncio
async def test_approve_idempotent(session, make_user):
    client = make_user(session, role=UserRole.CLIENT)
    sales = make_user(session, role=UserRole.SALES)
    dealer = make_user(session, role=UserRole.DEALER)
    head = make_user(session, role=UserRole.HEAD_OF_SALES)
    await session.flush()
    lead = await _take_lead(session, client.id, sales.id)
    svc = LeadApprovalService(session)
    approval, _ = await svc.request(
        sales_user_id=sales.id, lead_id=lead.id, proposed_dealer_id=dealer.id
    )

    await svc.approve(approval.id, head_user_id=head.id)
    _, err = await svc.approve(approval.id, head_user_id=head.id)
    assert err == "already_decided"
