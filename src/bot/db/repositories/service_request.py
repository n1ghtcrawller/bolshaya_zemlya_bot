from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import ServiceIssueType, ServiceRequestStatus
from bot.db.models.service_request import ServiceRequest


class ServiceRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, request_id: int) -> ServiceRequest | None:
        return await self._session.get(ServiceRequest, request_id)

    async def list_by_user(
        self, user_id: int, *, limit: int = 20
    ) -> Sequence[ServiceRequest]:
        stmt = (
            select(ServiceRequest)
            .where(ServiceRequest.user_id == user_id)
            .order_by(ServiceRequest.created_at.desc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def list_for_dealer(
        self,
        dealer_user_id: int,
        *,
        include_unassigned: bool = True,
        limit: int = 50,
    ) -> Sequence[ServiceRequest]:
        """Свои обращения + общая очередь без назначенного дилера."""
        stmt = select(ServiceRequest)
        if include_unassigned:
            stmt = stmt.where(
                or_(
                    ServiceRequest.assigned_dealer_id == dealer_user_id,
                    ServiceRequest.assigned_dealer_id.is_(None),
                )
            )
        else:
            stmt = stmt.where(ServiceRequest.assigned_dealer_id == dealer_user_id)
        stmt = stmt.order_by(ServiceRequest.created_at.desc()).limit(limit)
        return (await self._session.scalars(stmt)).all()

    async def create(
        self,
        *,
        user_id: int,
        issue_type: ServiceIssueType,
        equipment: str | None,
        description: str,
        contact_phone: str,
    ) -> ServiceRequest:
        request = ServiceRequest(
            user_id=user_id,
            issue_type=issue_type,
            equipment=equipment,
            description=description,
            contact_phone=contact_phone,
            status=ServiceRequestStatus.NEW,
        )
        self._session.add(request)
        await self._session.flush()
        return request

    async def assign_dealer(
        self, request: ServiceRequest, dealer_user_id: int
    ) -> ServiceRequest:
        request.assigned_dealer_id = dealer_user_id
        request.status = ServiceRequestStatus.IN_PROGRESS
        await self._session.flush()
        return request

    async def update_status(
        self, request: ServiceRequest, status: ServiceRequestStatus
    ) -> ServiceRequest:
        request.status = status
        await self._session.flush()
        return request
