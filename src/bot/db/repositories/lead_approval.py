from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ApprovalStatus
from bot.db.models.lead_approval import LeadApproval


class LeadApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, approval_id: int) -> LeadApproval | None:
        return await self._session.get(LeadApproval, approval_id)

    async def list_pending(self, *, limit: int = 50) -> Sequence[LeadApproval]:
        stmt = (
            select(LeadApproval)
            .where(LeadApproval.status == ApprovalStatus.PENDING)
            .order_by(LeadApproval.created_at.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def list_by_sales(
        self, sales_user_id: int, *, limit: int = 20
    ) -> Sequence[LeadApproval]:
        stmt = (
            select(LeadApproval)
            .where(LeadApproval.sales_user_id == sales_user_id)
            .order_by(LeadApproval.created_at.desc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def has_pending_for_lead(self, lead_id: int) -> bool:
        stmt = select(LeadApproval.id).where(
            LeadApproval.lead_id == lead_id,
            LeadApproval.status == ApprovalStatus.PENDING,
        )
        return (await self._session.scalar(stmt)) is not None

    async def create(
        self,
        *,
        lead_id: int,
        sales_user_id: int,
        proposed_dealer_id: int,
    ) -> LeadApproval:
        approval = LeadApproval(
            lead_id=lead_id,
            sales_user_id=sales_user_id,
            proposed_dealer_id=proposed_dealer_id,
            status=ApprovalStatus.PENDING,
        )
        self._session.add(approval)
        await self._session.flush()
        return approval

    async def decide(
        self,
        approval: LeadApproval,
        *,
        status: ApprovalStatus,
        decision_by_user_id: int,
        decision_at: datetime,
        note: str | None = None,
    ) -> LeadApproval:
        approval.status = status
        approval.decision_by_user_id = decision_by_user_id
        approval.decision_at = decision_at
        if note is not None:
            approval.decision_note = note
        await self._session.flush()
        return approval
