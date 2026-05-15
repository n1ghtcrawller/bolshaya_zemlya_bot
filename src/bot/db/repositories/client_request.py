from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.enums import RequestStatus
from bot.db.models.client_request import ClientRequest


class ClientRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, request_id: int) -> ClientRequest | None:
        return await self._session.get(ClientRequest, request_id)

    async def list_by_user(
        self, user_id: int, *, limit: int = 20, offset: int = 0
    ) -> Sequence[ClientRequest]:
        stmt = (
            select(ClientRequest)
            .where(ClientRequest.user_id == user_id)
            .order_by(ClientRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.scalars(stmt)
        return result.all()

    async def list_by_dealer(
        self,
        dealer_user_id: int,
        *,
        statuses: Sequence[RequestStatus] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[ClientRequest]:
        stmt = select(ClientRequest).where(ClientRequest.assigned_dealer_id == dealer_user_id)
        if statuses:
            stmt = stmt.where(ClientRequest.status.in_(statuses))
        stmt = (
            stmt.order_by(ClientRequest.created_at.desc()).limit(limit).offset(offset)
        )
        result = await self._session.scalars(stmt)
        return result.all()

    async def count_by_dealer_grouped(
        self, dealer_user_id: int
    ) -> dict[RequestStatus, int]:
        stmt = (
            select(ClientRequest.status, func.count())
            .where(ClientRequest.assigned_dealer_id == dealer_user_id)
            .group_by(ClientRequest.status)
        )
        rows = await self._session.execute(stmt)
        return {status: int(count) for status, count in rows.all()}

    async def count_grouped(self) -> dict[RequestStatus, int]:
        stmt = select(ClientRequest.status, func.count()).group_by(ClientRequest.status)
        rows = await self._session.execute(stmt)
        return {status: int(count) for status, count in rows.all()}

    async def list_unassigned(
        self, *, limit: int = 20, offset: int = 0
    ) -> Sequence[ClientRequest]:
        stmt = (
            select(ClientRequest)
            .where(
                ClientRequest.status == RequestStatus.NEW,
                ClientRequest.assigned_sales_id.is_(None),
                ClientRequest.assigned_dealer_id.is_(None),
            )
            .order_by(ClientRequest.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.scalars(stmt)
        return result.all()

    async def list_by_sales(
        self,
        sales_user_id: int,
        *,
        statuses: Sequence[RequestStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ClientRequest]:
        stmt = select(ClientRequest).where(ClientRequest.assigned_sales_id == sales_user_id)
        if statuses:
            stmt = stmt.where(ClientRequest.status.in_(statuses))
        stmt = (
            stmt.order_by(ClientRequest.created_at.desc()).limit(limit).offset(offset)
        )
        result = await self._session.scalars(stmt)
        return result.all()

    async def update_status(
        self, request: ClientRequest, status: RequestStatus
    ) -> ClientRequest:
        request.status = status
        await self._session.flush()
        return request

    async def assign_sales(
        self, request: ClientRequest, sales_user_id: int, status: RequestStatus
    ) -> ClientRequest:
        request.assigned_sales_id = sales_user_id
        request.status = status
        await self._session.flush()
        return request

    async def assign_dealer(
        self, request: ClientRequest, dealer_user_id: int, status: RequestStatus
    ) -> ClientRequest:
        request.assigned_dealer_id = dealer_user_id
        request.status = status
        await self._session.flush()
        return request

    async def create(
        self,
        *,
        user_id: int,
        contact_name: str,
        contact_phone: str,
        comment: str | None,
    ) -> ClientRequest:
        request = ClientRequest(
            user_id=user_id,
            contact_name=contact_name,
            contact_phone=contact_phone,
            comment=comment,
            status=RequestStatus.NEW,
        )
        self._session.add(request)
        await self._session.flush()
        return request
