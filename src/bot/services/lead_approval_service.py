from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ApprovalStatus, RequestStatus
from bot.db.models.lead_approval import LeadApproval
from bot.db.repositories.client_request import ClientRequestRepository
from bot.db.repositories.lead_approval import LeadApprovalRepository
from bot.db.repositories.user import UserRepository
from bot.logger import get_logger

log = get_logger(__name__)


class LeadApprovalService:
    """Эскалация передачи лидов на HeadOfSales.

    Sales создаёт запись `pending`, HeadOfSales одобряет или отклоняет.
    При одобрении лид реально передаётся диллеру (status=transferred_to_dealer).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LeadApprovalRepository(session)
        self._leads = ClientRequestRepository(session)
        self._users = UserRepository(session)

    async def request(
        self, *, sales_user_id: int, lead_id: int, proposed_dealer_id: int
    ) -> tuple[LeadApproval | None, str | None]:
        lead = await self._leads.get_by_id(lead_id)
        if lead is None:
            return None, "lead_not_found"
        if lead.assigned_sales_id != sales_user_id:
            return None, "not_owner"
        if lead.status != RequestStatus.IN_PROGRESS:
            return None, "not_in_progress"
        if await self._repo.has_pending_for_lead(lead_id):
            return None, "duplicate_pending"

        approval = await self._repo.create(
            lead_id=lead_id,
            sales_user_id=sales_user_id,
            proposed_dealer_id=proposed_dealer_id,
        )
        log.info(
            "lead_approval_requested",
            approval_id=approval.id,
            lead_id=lead_id,
            sales_id=sales_user_id,
            dealer_id=proposed_dealer_id,
        )
        return approval, None

    async def list_pending(self) -> Sequence[LeadApproval]:
        return await self._repo.list_pending()

    async def get(self, approval_id: int) -> LeadApproval | None:
        return await self._repo.get_by_id(approval_id)

    async def approve(
        self, approval_id: int, *, head_user_id: int, note: str | None = None
    ) -> tuple[LeadApproval | None, str | None]:
        approval = await self._repo.get_by_id(approval_id)
        if approval is None:
            return None, "not_found"
        if approval.status != ApprovalStatus.PENDING:
            return approval, "already_decided"

        lead = await self._leads.get_by_id(approval.lead_id)
        if lead is None:
            return approval, "lead_not_found"

        # передача лида диллеру от имени sales-автора
        await self._leads.assign_dealer(
            lead, approval.proposed_dealer_id, RequestStatus.TRANSFERRED_TO_DEALER
        )
        approval = await self._repo.decide(
            approval,
            status=ApprovalStatus.APPROVED,
            decision_by_user_id=head_user_id,
            decision_at=datetime.now(tz=timezone.utc),
            note=note,
        )
        log.info(
            "lead_approval_approved",
            approval_id=approval.id,
            lead_id=approval.lead_id,
            head_id=head_user_id,
        )
        return approval, None

    async def reject(
        self, approval_id: int, *, head_user_id: int, note: str | None = None
    ) -> tuple[LeadApproval | None, str | None]:
        approval = await self._repo.get_by_id(approval_id)
        if approval is None:
            return None, "not_found"
        if approval.status != ApprovalStatus.PENDING:
            return approval, "already_decided"
        approval = await self._repo.decide(
            approval,
            status=ApprovalStatus.REJECTED,
            decision_by_user_id=head_user_id,
            decision_at=datetime.now(tz=timezone.utc),
            note=note,
        )
        log.info(
            "lead_approval_rejected",
            approval_id=approval.id,
            lead_id=approval.lead_id,
            head_id=head_user_id,
        )
        return approval, None
